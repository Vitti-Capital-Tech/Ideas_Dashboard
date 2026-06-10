/**
 * Safely copies text to the clipboard, falling back to a legacy text-area selection
 * method if the modern Clipboard API is blocked (e.g. by a Permissions Policy
 * inside an iframe context).
 * 
 * @param {string} text The text to copy
 * @returns {Promise<boolean>} Resolves to true if the copy succeeded, false otherwise
 */
export function copyToClipboard(text) {
  if (typeof window === 'undefined') {
    return Promise.resolve(false);
  }

  // Try using the modern Clipboard API first
  if (navigator.clipboard && typeof navigator.clipboard.writeText === 'function') {
    return navigator.clipboard.writeText(text)
      .then(() => true)
      .catch((err) => {
        console.warn('Modern Clipboard API failed, attempting fallback:', err);
        return fallbackCopy(text);
      });
  }

  // Fallback to legacy execCommand method
  return Promise.resolve(fallbackCopy(text));
}

function fallbackCopy(text) {
  try {
    const textArea = document.createElement('textarea');
    textArea.value = text;
    
    // Position off-screen to prevent scrolling or visual disruption
    textArea.style.position = 'fixed';
    textArea.style.top = '0';
    textArea.style.left = '0';
    textArea.style.width = '2em';
    textArea.style.height = '2em';
    textArea.style.padding = '0';
    textArea.style.border = 'none';
    textArea.style.outline = 'none';
    textArea.style.boxShadow = 'none';
    textArea.style.background = 'transparent';
    
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();
    
    const successful = document.execCommand('copy');
    document.body.removeChild(textArea);
    
    return !!successful;
  } catch (err) {
    console.error('Fallback copy failed:', err);
    return false;
  }
}
