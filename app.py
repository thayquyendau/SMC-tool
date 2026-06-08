import io
import zipfile
from pathlib import Path
from tempfile import SpooledTemporaryFile

import streamlit as st
from PIL import Image, UnidentifiedImageError


st.set_page_config(page_title="Batch Image Crop Tool", layout="wide")
st.title("Batch Image Crop Tool (Streamlit Cloud)")
st.caption("Upload ảnh, xử lý ngay, và tải ZIP kết quả.")


def crop_with_repo_logic(img: Image.Image) -> Image.Image:
    """Crop logic: center 1/3 width, top half. (Removed final 1/2 crop.)"""
    rgb = img.convert("RGB")
    w, h = rgb.size

    # Too small to crop safely -> return original RGB image
    if w < 3 or h < 2:
        return rgb

    first_box = (w // 3, 0, 2 * w // 3, h // 2)
    first = rgb.crop(first_box)
    # Return the first crop directly; do not perform the additional half-height crop.
    return first


def safe_output_ext(input_name: str) -> str:
    ext = Path(input_name).suffix.lower()
    if ext in {".jpg", ".jpeg"}:
        return ".jpg"
    if ext == ".png":
        return ".png"
    return ".jpg"


def save_image_to_bytes(img: Image.Image, ext: str) -> bytes:
    buf = io.BytesIO()
    if ext == ".png":
        img.save(buf, format="PNG", optimize=True)
    else:
        img.save(buf, format="JPEG", quality=92, optimize=True)
    return buf.getvalue()


def build_output_name(input_name: str, ext: str) -> str:
    stem = Path(input_name).stem
    return f"{stem}_cropped{ext}"


if "result_zip" not in st.session_state:
    st.session_state.result_zip = None
if "stats" not in st.session_state:
    st.session_state.stats = None
if "errors" not in st.session_state:
    st.session_state.errors = []
if "last_upload_signature" not in st.session_state:
    st.session_state.last_upload_signature = None

uploaded_files = st.file_uploader(
    "1) Tải ảnh lên (nhiều ảnh cùng lúc)",
    type=["jpg", "jpeg", "png", "bmp", "webp", "tiff"],
    accept_multiple_files=True,
    help="Khuyến nghị 50-100 ảnh/lượt để ổn định trên Streamlit Cloud.",
    key="uploads",
)

# Nút reset: xóa các session state liên quan để tải ảnh mới
if st.button("Reset (Tải ảnh mới)"):
    for k in ("result_zip", "stats", "errors", "last_upload_signature", "uploads"):
        if k in st.session_state:
            st.session_state[k] = [] if k == "errors" else None
    st.experimental_rerun()

if uploaded_files:
    total_upload = len(uploaded_files)
    st.info(f"Đã upload: {total_upload} ảnh")
    if total_upload > 100:
        st.warning("Bạn đang upload hơn 100 ảnh. Nếu chậm, nên giảm còn 50-100 ảnh/lượt.")

    total_size_mb = sum(getattr(f, "size", 0) for f in uploaded_files) / (1024 * 1024)
    avg_size_mb = (total_size_mb / total_upload) if total_upload else 0
    if avg_size_mb >= 8 or total_size_mb >= 700:
        st.warning(
            "Phát hiện ảnh dung lượng lớn hoặc batch nặng. "
            "Khuyến nghị giảm batch size xuống 50 ảnh/lượt."
        )

    upload_signature = tuple((f.name, getattr(f, "size", 0)) for f in uploaded_files)
    if upload_signature != st.session_state.last_upload_signature:
        progress = st.progress(0)
        status = st.empty()

        success_count = 0
        error_count = 0
        errors = []

        spooled = SpooledTemporaryFile(max_size=50 * 1024 * 1024, mode="w+b")
        with zipfile.ZipFile(spooled, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
            total = len(uploaded_files)
            for idx, uploaded in enumerate(uploaded_files, start=1):
                name = uploaded.name
                status.text(f"Đang xử lý {idx}/{total}: {name}")
                try:
                    raw = uploaded.read()
                    in_img = Image.open(io.BytesIO(raw))
                    cropped = crop_with_repo_logic(in_img)

                    out_ext = safe_output_ext(name)
                    out_name = build_output_name(name, out_ext)
                    out_bytes = save_image_to_bytes(cropped, out_ext)
                    zf.writestr(out_name, out_bytes)

                    success_count += 1
                except (UnidentifiedImageError, OSError, ValueError) as e:
                    error_count += 1
                    errors.append(f"{name}: {e}")
                except Exception as e:
                    error_count += 1
                    errors.append(f"{name}: {e}")

                progress.progress(int(idx * 100 / total))

        spooled.seek(0)
        zip_bytes = spooled.read()
        spooled.close()

        st.session_state.result_zip = zip_bytes
        st.session_state.stats = {
            "total": len(uploaded_files),
            "success": success_count,
            "error": error_count,
        }
        st.session_state.errors = errors
        st.session_state.last_upload_signature = upload_signature

        status.text("Xử lý hoàn tất.")

if st.session_state.stats:
    s = st.session_state.stats
    c1, c2, c3 = st.columns(3)
    c1.metric("Tổng ảnh upload", s["total"])
    c2.metric("Xử lý thành công", s["success"])
    c3.metric("Ảnh lỗi", s["error"])

if st.session_state.errors:
    with st.expander("Danh sách ảnh lỗi", expanded=False):
        for err in st.session_state.errors:
            st.write(f"- {err}")

if st.session_state.result_zip:
    st.download_button(
        label="2) Tải ảnh đã cắt (.zip)",
        data=st.session_state.result_zip,
        file_name="cropped_images.zip",
        mime="application/zip",
        use_container_width=True,
    )


