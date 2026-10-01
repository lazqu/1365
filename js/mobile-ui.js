/**
 * 📱 1365 자원봉사 탐색기 - 모바일 UI & 터치 컨트롤러 (js/mobile-ui.js)
 */

document.addEventListener('DOMContentLoaded', () => {
  initMobileFilterAccordion();
  initDesktopFilterToggle();
  initResponsiveResizeHandler();
  initFloatingScrollControls();
  updateActiveFilterBadgeCount();
});

function initFloatingScrollControls() {
  const topButton = document.getElementById('scrollToResultsTop');
  const paginationButton = document.getElementById('scrollToPagination');
  const resultsHeader = document.querySelector('.results-header');
  const pagination = document.getElementById('paginationContainer');
  if (!topButton || !paginationButton || !resultsHeader || !pagination) return;

  const updateVisibility = () => {
    const isMobile = window.matchMedia('(max-width: 1024px)').matches;
    const paginationVisible = getComputedStyle(pagination).display !== 'none';
    const paginationRect = pagination.getBoundingClientRect();
    const paginationBelowViewport = paginationVisible && paginationRect.top > window.innerHeight;
    const paginationInViewport = paginationVisible && paginationRect.bottom > 0 && paginationRect.top < window.innerHeight;

    topButton.classList.toggle('is-visible', isMobile && window.scrollY > 300 && !paginationInViewport);
    paginationButton.classList.toggle('is-visible', isMobile && paginationBelowViewport);
  };

  topButton.addEventListener('click', () => {
    const top = window.scrollY + resultsHeader.getBoundingClientRect().top - 12;
    window.scrollTo({ top: Math.max(0, top), behavior: 'smooth' });
  });

  paginationButton.addEventListener('click', () => {
    const top = window.scrollY + pagination.getBoundingClientRect().top - window.innerHeight + pagination.getBoundingClientRect().height + 12;
    window.scrollTo({ top: Math.max(0, top), behavior: 'smooth' });
  });

  window.addEventListener('scroll', updateVisibility, { passive: true });
  window.addEventListener('resize', updateVisibility);
  new MutationObserver(updateVisibility).observe(pagination, {
    attributes: true,
    attributeFilter: ['style'],
    childList: true
  });
  updateVisibility();
}

/**
 * 모바일 필터 접이식(Accordion) 토글 초기화
 */
function initMobileFilterAccordion() {
  const toggleBtn = document.getElementById('btnMobileFilterToggle');
  const filterWrapper = document.getElementById('sidebarContent');
  const toggleIcon = document.getElementById('mobileFilterIcon');

  if (!toggleBtn || !filterWrapper) return;

  toggleBtn.addEventListener('click', (e) => {
    e.preventDefault();
    const isOpen = filterWrapper.classList.toggle('is-open');

    if (toggleIcon) {
      if (isOpen) {
        toggleIcon.classList.add('is-open');
        toggleIcon.textContent = '▲';
      } else {
        toggleIcon.classList.remove('is-open');
        toggleIcon.textContent = '▼';
      }
    }

    toggleBtn.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
  });
}

function initDesktopFilterToggle() {
  const toggleBtn = document.getElementById('btnDesktopFilterToggle');
  const main = document.querySelector('main');
  if (!toggleBtn || !main) return;

  toggleBtn.addEventListener('click', () => {
    const isCollapsed = main.classList.toggle('filters-collapsed');
    const label = isCollapsed ? '필터 보이기' : '필터 숨기기';
    toggleBtn.setAttribute('aria-expanded', String(!isCollapsed));
    toggleBtn.setAttribute('aria-label', label);
    toggleBtn.title = label;
    toggleBtn.textContent = isCollapsed ? '☰ 필터' : '◀ 필터';
  });
}

/**
 * 활성화된 검색 조건 개수를 모바일 토글 버튼에 동적으로 표시
 */
function updateActiveFilterBadgeCount() {
  const badgeEl = document.getElementById('mobileFilterBadgeCount');
  if (!badgeEl) return;

  let activeCount = 0;

  ['recruitingOnly', 'adultPosbl', 'youthPosbl'].forEach((id) => {
    const checkbox = document.getElementById(id);
    if (checkbox && checkbox.checked) activeCount++;
  });

  const sido = document.getElementById('sidoSelect');
  if (sido && sido.value) activeCount++;

  const location = document.getElementById('locText');
  if (location && location.value.trim()) activeCount++;

  const useKeywords = document.getElementById('useKwds');
  if (useKeywords && useKeywords.checked) {
    ['includeKwds', 'excludeKwds'].forEach((id) => {
      const input = document.getElementById(id);
      if (input && input.value.trim()) activeCount++;
    });
  }

  const useTargetDate = document.getElementById('useTargetDate');
  const targetDate = document.getElementById('targetDate');
  if (useTargetDate && useTargetDate.checked && targetDate && targetDate.value) {
    activeCount++;
  }

  if (activeCount > 0) {
    badgeEl.textContent = `· 조건 ${activeCount}`;
    badgeEl.style.display = 'inline-block';
  } else {
    badgeEl.textContent = '';
    badgeEl.style.display = 'none';
  }
}

/**
 * 윈도우 리사이즈 시 데스크톱 ↔ 모바일 전환 스타일 보정
 */
function initResponsiveResizeHandler() {
  const breakpoint = window.matchMedia('(max-width: 1024px)');
  let wasStacked = breakpoint.matches;

  const syncLayoutState = (isStacked) => {
    const main = document.querySelector('main');
    const sidebarContent = document.getElementById('sidebarContent');
    const mobileToggle = document.getElementById('btnMobileFilterToggle');
    const desktopToggle = document.getElementById('btnDesktopFilterToggle');
    if (!main || !sidebarContent || !mobileToggle || !desktopToggle) return;

    main.classList.remove('filters-collapsed');
    sidebarContent.classList.remove('is-open');
    mobileToggle.setAttribute('aria-expanded', 'false');
    const icon = document.getElementById('mobileFilterIcon');
    if (icon) {
      icon.classList.remove('is-open');
      icon.textContent = '▼';
    }

    desktopToggle.setAttribute('aria-expanded', 'true');
    desktopToggle.setAttribute('aria-label', '필터 숨기기');
    desktopToggle.title = '필터 숨기기';
    desktopToggle.textContent = '◀ 필터';
  };

  syncLayoutState(wasStacked);

  window.addEventListener('resize', () => {
    if (breakpoint.matches !== wasStacked) {
      wasStacked = breakpoint.matches;
      syncLayoutState(wasStacked);
    }
  });

  // 필터 변경 시 모바일 뱃지 수치 자동 업데이트 바인딩
  const filterFormInputs = document.querySelectorAll('.panel-sidebar input, .panel-sidebar select');
  filterFormInputs.forEach((input) => {
    input.addEventListener('change', updateActiveFilterBadgeCount);
    input.addEventListener('input', updateActiveFilterBadgeCount);
  });
}
