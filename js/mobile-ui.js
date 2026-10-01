/**
 * 📱 1365 자원봉사 탐색기 - 모바일 UI & 터치 컨트롤러 (js/mobile-ui.js)
 */

document.addEventListener('DOMContentLoaded', () => {
  initMobileFilterAccordion();
  initResponsiveResizeHandler();
  updateActiveFilterBadgeCount();
});

/**
 * 모바일 필터 접이식(Accordion) 토글 초기화
 */
function initMobileFilterAccordion() {
  const toggleBtn = document.getElementById('btnMobileFilterToggle');
  const filterWrapper = document.getElementById('mobileFilterContent');
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
    badgeEl.textContent = `(${activeCount})`;
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
  window.addEventListener('resize', () => {
    const filterWrapper = document.getElementById('mobileFilterContent');
    if (!filterWrapper) return;

    if (window.innerWidth > 768) {
      // 데스크톱 뷰포트 전환 시 아코디언 클래스와 무관하게 필터 보이도록
      filterWrapper.classList.remove('is-open');
    }
  });

  // 필터 변경 시 모바일 뱃지 수치 자동 업데이트 바인딩
  const filterFormInputs = document.querySelectorAll('.panel-sidebar input, .panel-sidebar select');
  filterFormInputs.forEach((input) => {
    input.addEventListener('change', updateActiveFilterBadgeCount);
    input.addEventListener('input', updateActiveFilterBadgeCount);
  });
}
