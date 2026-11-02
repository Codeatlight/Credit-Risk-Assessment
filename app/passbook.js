// A scrollbar shaped like a bank account: scrolling down deposits, scrolling up withdraws.
// Runs in the main page, because Streamlit's scrolling area lives there.
(() => {
  if (window.passbookStarted) return;
  window.passbookStarted = true;

  const TOP_BALANCE = 2500000;
  const HIDE_AFTER_MS = 1000;
  const rupees = value => "₹" + Math.round(value).toLocaleString("en-IN");
  const scroller = () => document.querySelector('[data-testid="stMain"]');
  let watched = null, lastBalance = 0, moved = 0, hideTimer = null;

  function build() {
    const app = document.querySelector(".stApp");
    if (!app) return;
    const rail = document.createElement("aside");
    rail.id = "passbook";
    rail.setAttribute("aria-hidden", "true");
    rail.innerHTML = '<small>Balance</small><strong class="amount">₹0</strong>' +
      '<div class="tube"><div class="fill"></div><div class="coin">₹</div></div>' +
      '<div class="slip"></div>';
    app.appendChild(rail);
    const tube = rail.querySelector(".tube");
    const seek = event => {
      const box = tube.getBoundingClientRect();
      const area = scroller();
      const share = Math.min(Math.max((event.clientY - box.top) / box.height, 0), 1);
      area.scrollTop = share * (area.scrollHeight - area.clientHeight);
    };
    tube.addEventListener("pointerdown", event => {
      tube.setPointerCapture(event.pointerId);
      seek(event);
      tube.addEventListener("pointermove", seek);
    });
    tube.addEventListener("pointerup", () => tube.removeEventListener("pointermove", seek));
  }

  function showSlip(rail, change) {
    moved += change;
    const slip = rail.querySelector(".slip");
    slip.textContent = moved >= 0 ? `+${rupees(moved)} deposited` : `-${rupees(-moved)} withdrawn`;
    slip.className = `slip show ${moved >= 0 ? "in" : "out"}`;
    rail.querySelector(".coin").classList.toggle("flip");
    clearTimeout(hideTimer);
    hideTimer = setTimeout(() => {
      slip.className = "slip";
      moved = 0;
    }, HIDE_AFTER_MS);
  }

  function update(withSlip) {
    const rail = document.getElementById("passbook");
    const area = scroller();
    if (!rail || !area) return;
    const room = area.scrollHeight - area.clientHeight;
    const share = room > 0 ? area.scrollTop / room : 0;
    const balance = Math.round((share * TOP_BALANCE) / 100) * 100;
    rail.querySelector(".amount").textContent = rupees(balance);
    rail.querySelector(".fill").style.height = `${share * 100}%`;
    rail.querySelector(".coin").style.top = `${share * 100}%`;
    rail.classList.toggle("idle", room <= 0);
    if (withSlip && balance !== lastBalance) showSlip(rail, balance - lastBalance);
    lastBalance = balance;
  }

  // Streamlit redraws parts of the page, so keep checking the rail and scroll listener still exist
  setInterval(() => {
    if (!document.getElementById("passbook")) build();
    const area = scroller();
    if (area && area !== watched) {
      watched = area;
      area.addEventListener("scroll", () => update(true), { passive: true });
    }
    update(false);
  }, 400);
})();
