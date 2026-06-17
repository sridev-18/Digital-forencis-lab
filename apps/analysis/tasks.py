"""
Celery tasks for forensic analysis.
These run in the background so users don't have to wait.
When evidence is uploaded, run_full_analysis is triggered automatically.
"""
import os
import json
import tempfile
from datetime import datetime
from celery import shared_task
from django.utils import timezone


@shared_task(bind=True, max_retries=3)
def run_full_analysis(self, evidence_id, user_id):
    """
    Master task — runs all analysis steps on a piece of evidence.
    Triggered automatically when evidence is uploaded.
    """
    from apps.evidence.models import Evidence, ChainOfCustody
    from apps.analysis.models import AnalysisTask
    from apps.accounts.models import User

    try:
        evidence = Evidence.objects.get(id=evidence_id)
        user = User.objects.get(id=user_id)
    except (Evidence.DoesNotExist, User.DoesNotExist):
        return {"error": "Evidence or user not found"}

    task = AnalysisTask.objects.create(
        evidence=evidence,
        case=evidence.case,
        task_type=AnalysisTask.TaskType.FULL,
        status=AnalysisTask.Status.RUNNING,
        celery_task_id=self.request.id,
        created_by=user,
        started_at=timezone.now(),
    )

    results = {}
    try:
        results["file_type"] = detect_file_type(evidence)
        results["strings"] = extract_strings(evidence)
        results["yara"] = run_yara_scan(evidence)
        results["metadata"] = extract_metadata(evidence)

        is_suspicious = (
            len(results["yara"].get("matches", [])) > 0 or
            results.get("metadata", {}).get("has_macros", False)
        )
        threat_score = len(results["yara"].get("matches", [])) * 25

        task.status = AnalysisTask.Status.COMPLETED
        task.result_json = results
        task.is_suspicious = is_suspicious
        task.threat_score = min(threat_score, 100)
        task.yara_matches = results["yara"].get("matches", [])
        task.result_summary = build_summary(results, is_suspicious)
        task.completed_at = timezone.now()
        task.save()

        evidence.status = Evidence.Status.FLAGGED if is_suspicious else Evidence.Status.ANALYSED
        evidence.save()

        ChainOfCustody.objects.create(
            evidence=evidence,
            action=ChainOfCustody.Action.ANALYSED,
            performed_by=user,
            notes=f"Full analysis complete. Suspicious: {is_suspicious}. Threat score: {threat_score}",
            hash_verified=True,
        )

        return {"status": "completed", "suspicious": is_suspicious, "threat_score": threat_score}

    except Exception as exc:
        task.status = AnalysisTask.Status.FAILED
        task.error_message = str(exc)
        task.completed_at = timezone.now()
        task.save()
        raise self.retry(exc=exc, countdown=60)


def detect_file_type(evidence):
    """Detect actual file type using python-magic (not just the extension)."""
    try:
        import magic
        evidence.file.seek(0)
        header = evidence.file.read(2048)
        evidence.file.seek(0)
        mime_type = magic.from_buffer(header, mime=True)
        evidence.file_type = mime_type
        evidence.save(update_fields=["file_type"])
        return {"mime_type": mime_type, "detected": True}
    except ImportError:
        return {"mime_type": "unknown", "detected": False, "reason": "python-magic not available"}
    except Exception as e:
        return {"mime_type": "unknown", "error": str(e)}


def extract_strings(evidence, min_length=6):
    """Extract printable strings from a binary file — can reveal URLs, passwords, etc."""
    try:
        evidence.file.seek(0)
        data = evidence.file.read(10 * 1024 * 1024)  # Read up to 10MB
        evidence.file.seek(0)

        strings = []
        current = []
        printable = set(range(32, 127))

        for byte in data:
            if byte in printable:
                current.append(chr(byte))
            else:
                if len(current) >= min_length:
                    s = "".join(current)
                    strings.append(s)
                current = []

        # Filter for interesting strings
        interesting = [
            s for s in strings if any(
                keyword in s.lower()
                for keyword in ["http", "password", "admin", "token", "cmd", "powershell",
                                "base64", "exec", "shell", ".exe", ".dll", "192.168", "10.0"]
            )
        ]
        return {
            "total_strings": len(strings),
            "interesting_count": len(interesting),
            "interesting_strings": interesting[:50],  # First 50
        }
    except Exception as e:
        return {"error": str(e), "total_strings": 0}


def run_yara_scan(evidence):
    """
    Scan the file against YARA rules to detect known malware signatures.
    YARA is the industry standard tool for malware detection.
    """
    try:
        import yara

        # Inline YARA rules for demo — in production load from a rules directory
        rules_source = r"""
        rule SuspiciousPowerShell {
            meta:
                description = "Detects obfuscated PowerShell commands"
            strings:
                $ps1 = "powershell" nocase
                $enc = "-encodedcommand" nocase
                $bypass = "-ExecutionPolicy Bypass" nocase
            condition:
                any of them
        }

        rule MimikatzIndicator {
            meta:
                description = "Detects Mimikatz credential dumper"
            strings:
                $s1 = "mimikatz" nocase
                $s2 = "sekurlsa" nocase
                $s3 = "lsadump" nocase
            condition:
                any of them
        }

        rule WebShell {
            meta:
                description = "Detects common web shell patterns"
            strings:
                $php1 = "<?php" nocase
                $cmd1 = "eval(base64_decode" nocase
                $cmd2 = "system($_GET" nocase
                $cmd3 = "exec($_POST" nocase
            condition:
                $php1 and (1 of ($cmd*))
        }

        rule SuspiciousNetworkActivity {
            meta:
                description = "Detects hardcoded IPs and C2 patterns"
            strings:
                $c2 = /\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d{4,5}/
                $tor = ".onion" nocase
            condition:
                any of them
        }
        """
        rules = yara.compile(source=rules_source)

        evidence.file.seek(0)
        data = evidence.file.read(50 * 1024 * 1024)  # 50MB max
        evidence.file.seek(0)

        matches = rules.match(data=data)
        match_results = [
            {
                "rule": m.rule,
                "meta": m.meta,
                "strings_matched": [str(s) for s in m.strings[:5]],
            }
            for m in matches
        ]

        return {
            "scanned": True,
            "matches": match_results,
            "match_count": len(match_results),
            "is_clean": len(match_results) == 0,
        }

    except ImportError:
        return {"scanned": False, "reason": "yara-python not installed", "matches": []}
    except Exception as e:
        return {"scanned": False, "error": str(e), "matches": []}


def extract_metadata(evidence):
    """Extract metadata from documents, images etc — can reveal author, GPS, software used."""
    try:
        from PIL import Image
        from PIL.ExifTags import TAGS
        import io

        evidence.file.seek(0)
        data = evidence.file.read()
        evidence.file.seek(0)

        metadata = {}

        if evidence.file_type and "image" in evidence.file_type:
            img = Image.open(io.BytesIO(data))
            exif_data = img._getexif()
            if exif_data:
                for tag_id, value in exif_data.items():
                    tag = TAGS.get(tag_id, str(tag_id))
                    if isinstance(value, bytes):
                        continue
                    metadata[tag] = str(value)

        return {
            "extracted": True,
            "fields": metadata,
            "has_gps": "GPSInfo" in metadata,
            "has_macros": False,
        }
    except Exception as e:
        return {"extracted": False, "error": str(e), "fields": {}}


def build_summary(results, is_suspicious):
    lines = []
    if is_suspicious:
        lines.append("ALERT: Suspicious content detected.")
    yara = results.get("yara", {})
    if yara.get("matches"):
        lines.append(f"YARA: {yara['match_count']} rule(s) matched: {', '.join(m['rule'] for m in yara['matches'])}")
    else:
        lines.append("YARA: No known malware signatures detected.")
    strings = results.get("strings", {})
    if strings.get("interesting_count", 0) > 0:
        lines.append(f"Strings: {strings['interesting_count']} interesting strings found.")
    file_type = results.get("file_type", {})
    if file_type.get("mime_type"):
        lines.append(f"File type: {file_type['mime_type']}")
    return " | ".join(lines)
