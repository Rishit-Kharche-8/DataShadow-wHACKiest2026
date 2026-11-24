import os
import json
import math
import wave
import struct
import io
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()


def build_zero_pii_digest(before_audit: dict, after_audit: dict, compound: dict, clean_df) -> dict:
    """Constructs a strictly zero-PII JSON summary digest for AWS S3 & ElevenLabs."""
    return {
        "schema_version": "datashadow-v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "pii_guaranteed_stripped": True,
        "reid_risk_before_pct": before_audit["reid_risk_pct"],
        "reid_risk_after_pct": after_audit["reid_risk_pct"],
        "days_analyzed": int(len(clean_df)),
        "avg_sleep_hours": round(float(clean_df["sleep_hours"].mean()), 2) if "sleep_hours" in clean_df else None,
        "avg_late_screen_mins": round(float(clean_df["late_screen_mins"].mean()), 1) if "late_screen_mins" in clean_df else None,
        "compound_status": compound["status"],
        "compound_lift": compound["lift"],
        "compound_summary": compound["message"],
    }


def sync_digest_to_aws_s3(digest: dict) -> tuple[bool, str]:
    """Uploads strictly zero-PII JSON digest to encrypted AWS S3 bucket (with local fallback)."""
    bucket = os.getenv("AWS_S3_BUCKET", "").strip()
    access_key = os.getenv("AWS_ACCESS_KEY_ID", "").strip()
    secret_key = os.getenv("AWS_SECRET_ACCESS_KEY", "").strip()
    region = os.getenv("AWS_REGION", "ap-south-1").strip()

    object_key = f"digests/digest_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"

    if not (bucket and access_key and secret_key):
        return (
            False,
            f"Demo Vault Mode (no AWS keys in .env): Zero-PII JSON prepared for `s3://<bucket>/{object_key}` with SSE-AES256.",
        )

    try:
        import boto3

        s3 = boto3.client(
            "s3",
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region,
        )
        s3.put_object(
            Bucket=bucket,
            Key=object_key,
            Body=json.dumps(digest, indent=2).encode("utf-8"),
            ContentType="application/json",
            ServerSideEncryption="AES256",
        )
        return True, f"Synced zero-PII digest to encrypted AWS S3: `s3://{bucket}/{object_key}` (AES-256)"
    except Exception as exc:
        return False, f"AWS S3 fallback active ({exc})"


def _fallback_chime_wav() -> bytes:
    """Generates a gentle 1.2s offline audio cue when ElevenLabs API key is not configured."""
    sample_rate = 22050
    duration = 1.2
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        for i in range(int(sample_rate * duration)):
            freq = 523.25 if i < sample_rate * 0.6 else 659.25
            val = int(12000 * math.sin(2 * math.pi * freq * i / sample_rate))
            wf.writeframes(struct.pack("<h", val))
    return buf.getvalue()


def generate_elevenlabs_brief(digest: dict) -> tuple[str, bytes, str]:
    """Synthesizes a 30-sec screen-free spoken audit via ElevenLabs (with offline fallback)."""
    script = (
        f"DataShadow Privacy and Habit Brief. Your local audit reduced re-identification risk "
        f"from {digest['reid_risk_before_pct']} percent down to {digest['reid_risk_after_pct']} percent "
        f"by stripping identifiers and coarsening timestamps on-device. "
        f"{digest['compound_summary']} "
        f"Tonight, cut screen exposure 90 minutes before bed to protect tomorrow's focus."
    )

    api_key = os.getenv("ELEVENLABS_API_KEY", "").strip()
    voice_id = os.getenv("ELEVENLABS_VOICE_ID", "JBFqnCBsd6RMkjVDRZzb").strip()

    if not api_key:
        return (
            script,
            _fallback_chime_wav(),
            "Offline Audio Preview Mode (add ELEVENLABS_API_KEY in .env for live neural TTS)",
        )

    try:
        from elevenlabs.client import ElevenLabs

        client = ElevenLabs(api_key=api_key)
        audio_iter = client.text_to_speech.convert(
            text=script,
            voice_id=voice_id,
            model_id="eleven_multilingual_v2",
            output_format="mp3_44100_128",
        )
        audio_bytes = b"".join(chunk for chunk in audio_iter if chunk)
        return script, audio_bytes, "ElevenLabs Live Neural Voice Brief Generated"
    except Exception as exc:
        return script, _fallback_chime_wav(), f"ElevenLabs offline fallback ({exc})"
