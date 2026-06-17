from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from apps.accounts.models import AuditLog
from apps.cases.models import Case
from .models import Evidence, ChainOfCustody
from apps.analysis.tasks import run_full_analysis


@login_required
def evidence_upload_view(request, case_pk):
    case = get_object_or_404(Case, pk=case_pk)

    if request.method == "POST":
        uploaded_file = request.FILES.get("file")
        if not uploaded_file:
            messages.error(request, "No file selected.")
            return redirect("cases:detail", pk=case_pk)

        evidence = Evidence(
            case=case,
            file=uploaded_file,
            original_filename=uploaded_file.name,
            file_size=uploaded_file.size,
            evidence_type=request.POST.get("evidence_type", Evidence.EvidenceType.OTHER),
            description=request.POST.get("description", ""),
            source_device=request.POST.get("source_device", ""),
            source_location=request.POST.get("source_location", ""),
            acquisition_tool=request.POST.get("acquisition_tool", ""),
            uploaded_by=request.user,
        )

        # Compute hashes before saving
        evidence.compute_hashes()
        evidence.save()

        # Start chain of custody
        ChainOfCustody.objects.create(
            evidence=evidence,
            action=ChainOfCustody.Action.UPLOADED,
            performed_by=request.user,
            notes=f"File uploaded. SHA256: {evidence.sha256_hash}",
            hash_verified=True,
        )
        ChainOfCustody.objects.create(
            evidence=evidence,
            action=ChainOfCustody.Action.HASHED,
            performed_by=request.user,
            notes=f"MD5: {evidence.md5_hash} | SHA256: {evidence.sha256_hash}",
            hash_verified=True,
        )

        # Log the upload
        AuditLog.objects.create(
            user=request.user,
            action=AuditLog.Action.UPLOAD,
            resource_type="Evidence",
            resource_id=str(evidence.id),
            description=f"Uploaded {evidence.original_filename} to case {case.case_number}",
            ip_address=request.META.get("REMOTE_ADDR"),
        )

        # Kick off background analysis via Celery
        run_full_analysis.delay(evidence.id, request.user.id)

        messages.success(request, f"Evidence uploaded and queued for analysis. SHA256: {evidence.sha256_hash[:16]}...")
        return redirect("cases:detail", pk=case_pk)

    return render(request, "evidence/upload.html", {
        "case": case,
        "evidence_types": Evidence.EvidenceType.choices,
    })


@login_required
def evidence_detail_view(request, pk):
    evidence = get_object_or_404(Evidence, pk=pk)
    AuditLog.objects.create(
        user=request.user,
        action=AuditLog.Action.READ,
        resource_type="Evidence",
        resource_id=str(evidence.id),
        description=f"Viewed evidence {evidence.original_filename}",
        ip_address=request.META.get("REMOTE_ADDR"),
    )
    return render(request, "evidence/detail.html", {
        "evidence": evidence,
        "custody_chain": evidence.custody_chain.order_by("timestamp"),
        "analysis_tasks": evidence.analysis_tasks.order_by("-created_at"),
    })


@login_required
def verify_hash_view(request, pk):
    """Re-verify the file hash to confirm it hasn't been tampered with."""
    evidence = get_object_or_404(Evidence, pk=pk)
    original_sha256 = evidence.sha256_hash
    evidence.compute_hashes()
    is_intact = evidence.sha256_hash == original_sha256

    ChainOfCustody.objects.create(
        evidence=evidence,
        action=ChainOfCustody.Action.VERIFIED,
        performed_by=request.user,
        notes=f"Hash verification {'PASSED' if is_intact else 'FAILED'}. Current SHA256: {evidence.sha256_hash}",
        hash_verified=is_intact,
    )

    return JsonResponse({
        "intact": is_intact,
        "original_hash": original_sha256,
        "current_hash": evidence.sha256_hash,
        "message": "File integrity verified — untampered." if is_intact else "WARNING: File hash mismatch — possible tampering!",
    })
