// ---------- State ----------
let lastResumeText = "";
let lastJdText = "";

// ---------- Elements ----------
const resumeTextEl = document.getElementById("resume-text");
const jdTextEl = document.getElementById("jd-text");
const resumeFileEl = document.getElementById("resume-file");
const jdFileEl = document.getElementById("jd-file");
const analyzeBtn = document.getElementById("analyze-btn");
const analyzeStatus = document.getElementById("analyze-status");
const resultsSection = document.getElementById("results-section");
const chatSection = document.getElementById("chat-section");
const chatWindow = document.getElementById("chat-window");
const chatInput = document.getElementById("chat-input");
const chatSendBtn = document.getElementById("chat-send-btn");

// ---------- Analyze ----------
analyzeBtn.addEventListener("click", async () => {
  const resumeText = resumeTextEl.value.trim();
  const jdText = jdTextEl.value.trim();
  const resumeFile = resumeFileEl.files[0];
  const jdFile = jdFileEl.files[0];

  if (!resumeText && !resumeFile) {
    setStatus("Please paste or upload a resume.", true);
    return;
  }
  if (!jdText && !jdFile) {
    setStatus("Please paste or upload a job description.", true);
    return;
  }

  analyzeBtn.disabled = true;
  setStatus("Analyzing...");

  try {
    let response;

    if (resumeFile || jdFile) {
      const formData = new FormData();
      formData.append("resume_text", resumeText);
      formData.append("job_description", jdText);
      if (resumeFile) formData.append("resume_file", resumeFile);
      if (jdFile) formData.append("jd_file", jdFile);

      response = await fetch("/analyze", { method: "POST", body: formData });
    } else {
      response = await fetch("/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ resume_text: resumeText, job_description: jdText }),
      });
    }

    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      throw new Error(err.error || `Request failed (${response.status})`);
    }

    const data = await response.json();
    lastResumeText = resumeText;
    lastJdText = jdText;
    renderResults(data);
    setStatus("Done.");
  } catch (err) {
    console.error(err);
    setStatus(`Error: ${err.message}`, true);
  } finally {
    analyzeBtn.disabled = false;
  }
});

function setStatus(msg, isError = false) {
  analyzeStatus.textContent = msg;
  analyzeStatus.style.color = isError ? "#ff6b6b" : "";
}

// ---------- Render Results ----------
function renderResults(data) {
  resultsSection.classList.remove("hidden");
  chatSection.classList.remove("hidden");

  document.getElementById("total-score").textContent = data.totalScore ?? "--";
  document.getElementById("impact-score").textContent = data.impactScore ?? "--";

  renderChips("matched-keywords", data.matchedKeywords, "matched");
  renderChips("missing-keywords", data.missingKeywords, "missing");
  renderChips("action-verbs", data.actionVerbsFound, "");

  const checksList = document.getElementById("technical-checks");
  checksList.innerHTML = "";
  (data.checks || []).forEach((check) => {
    const li = document.createElement("li");
    const badge = document.createElement("span");
    badge.className = `status-badge ${check.status}`;
    badge.textContent = check.status;
    const text = document.createElement("span");
    text.textContent = `${check.name} — ${check.msg}`;
    li.appendChild(badge);
    li.appendChild(text);
    checksList.appendChild(li);
  });

  const suggestionsList = document.getElementById("suggestions-list");
  suggestionsList.innerHTML = "";
  (data.suggestions || []).forEach((s) => {
    const li = document.createElement("li");
    li.textContent = s;
    suggestionsList.appendChild(li);
  });

  resultsSection.scrollIntoView({ behavior: "smooth", block: "start" });
}

function renderChips(containerId, items, kind) {
  const container = document.getElementById(containerId);
  container.innerHTML = "";
  (items || []).forEach((item) => {
    const chip = document.createElement("span");
    chip.className = `chip ${kind}`;
    chip.textContent = item;
    container.appendChild(chip);
  });
  if (!items || items.length === 0) {
    const empty = document.createElement("span");
    empty.style.color = "var(--text-dim)";
    empty.textContent = "None found.";
    container.appendChild(empty);
  }
}

// ---------- Chat ----------
chatSendBtn.addEventListener("click", sendChatMessage);
chatInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter") sendChatMessage();
});

async function sendChatMessage() {
  const message = chatInput.value.trim();
  if (!message) return;

  appendChatMessage(message, "user");
  chatInput.value = "";
  chatSendBtn.disabled = true;

  try {
    const response = await fetch("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message,
        resume_text: lastResumeText,
        jd_text: lastJdText,
      }),
    });

    const data = await response.json();
    appendChatMessage(data.reply || "No response.", "bot");
  } catch (err) {
    console.error(err);
    appendChatMessage("Sorry, something went wrong reaching the coach.", "bot");
  } finally {
    chatSendBtn.disabled = false;
  }
}

function appendChatMessage(text, sender) {
  const msg = document.createElement("div");
  msg.className = `chat-msg ${sender}`;
  msg.textContent = text;
  chatWindow.appendChild(msg);
  chatWindow.scrollTop = chatWindow.scrollHeight;
}
