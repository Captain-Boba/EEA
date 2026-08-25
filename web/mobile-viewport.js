(() => {
  "use strict";

  const FORCED_DESKTOP_WIDTH = 1920;
  const LAYOUT_CLASS = "mobile-desktop-layout";
  const NOTICE_DISMISS_KEY = "eea-mobile-desktop-notice-dismissed";

  function isMobileDevice() {
    const userAgentDataMobile = navigator.userAgentData?.mobile === true;
    const mobileUserAgent = /Android|webOS|iPhone|iPad|iPod|IEMobile|Opera Mini/i.test(navigator.userAgent);
    const iPadDesktopUserAgent = navigator.platform === "MacIntel" && navigator.maxTouchPoints > 1;
    const compactTouchScreen = navigator.maxTouchPoints > 0
      && window.matchMedia("(pointer: coarse)").matches
      && Math.min(window.screen.width, window.screen.height) <= 600;
    return userAgentDataMobile || mobileUserAgent || iPadDesktopUserAgent || compactTouchScreen;
  }

  if (!isMobileDevice()) return;

  const viewport = document.getElementById("viewport-meta");
  if (!viewport) return;

  viewport.setAttribute(
    "content",
    `width=${FORCED_DESKTOP_WIDTH}, minimum-scale=0.1, maximum-scale=5, user-scalable=yes`,
  );
  document.documentElement.classList.add(LAYOUT_CLASS);

  function noticeWasDismissed() {
    try {
      return window.localStorage.getItem(NOTICE_DISMISS_KEY) === "true";
    } catch (_error) {
      return false;
    }
  }

  function rememberDismissal() {
    try {
      window.localStorage.setItem(NOTICE_DISMISS_KEY, "true");
    } catch (_error) {
      // The notice still closes when storage is unavailable.
    }
  }

  function initializeNotice() {
    const notice = document.getElementById("mobile-desktop-notice");
    const closeButton = document.getElementById("mobile-desktop-notice-close");
    if (!notice || !closeButton || noticeWasDismissed()) return;

    notice.hidden = false;
    closeButton.addEventListener("click", () => {
      rememberDismissal();
      notice.hidden = true;
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initializeNotice, {once: true});
  } else {
    initializeNotice();
  }
})();
