/**
 * Capture a JPEG frame from a <video> element using a <canvas>.
 * Returns base64 data URL or null on failure.
 */
export function captureFrame(video, canvas, width = 640, height = 480, quality = 0.7) {
  try {
    if (!video || video.readyState < 2) return null;
    canvas.width = width;
    canvas.height = height;
    const ctx = canvas.getContext("2d");
    ctx.drawImage(video, 0, 0, width, height);
    return canvas.toDataURL("image/jpeg", quality);
  } catch (e) {
    console.error("captureFrame error:", e);
    return null;
  }
}

/**
 * Generate a unique session ID.
 */
export function generateSessionId() {
  return `session_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
}
