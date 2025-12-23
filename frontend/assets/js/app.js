function getCurrentPage() {
  const path = window.location.pathname;
  const file = path.split("/").pop() || "index.html";
  return file.toLowerCase();
}

const API_BASE_URL = "http://127.0.0.1:8000";

function resolveUrl(url) {
  if (!url) return null;
  if (url.startsWith("http://") || url.startsWith("https://")) return url;
  if (url.startsWith("/")) return `${API_BASE_URL}${url}`;
  return url;
}

function escapeText(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

function appendUserBubble(container, text, imageFile, audioFile) {
  const bubble = document.createElement("div");
  bubble.className = "bubble bubble--user";

  const title = document.createElement("div");
  title.className = "bubble__title";
  title.textContent = "You";

  const body = document.createElement("div");
  body.className = "bubble__body";
  body.innerHTML = escapeText(text || "");

  const attachments = document.createElement("div");
  attachments.className = "bubble__attachments";

  let hasAttachments = false;
  if (imageFile) {
    hasAttachments = true;
    const pill = document.createElement("div");
    pill.className = "pill";
    pill.textContent = `Image: ${imageFile.name}`;
    attachments.appendChild(pill);
  }
  if (audioFile) {
    hasAttachments = true;
    const pill = document.createElement("div");
    pill.className = "pill";
    pill.textContent = `Audio: ${audioFile.name}`;
    attachments.appendChild(pill);
  }

  bubble.appendChild(title);
  bubble.appendChild(body);
  if (hasAttachments) bubble.appendChild(attachments);

  container.appendChild(bubble);
}

function appendAssistantBubble(container, payload) {
  const bubble = document.createElement("div");
  bubble.className = "bubble bubble--assistant";

  const title = document.createElement("div");
  title.className = "bubble__title";
  title.textContent = "Advisory";

  const body = document.createElement("div");
  body.className = "bubble__body";
  body.textContent = payload && typeof payload.response_text === "string" ? payload.response_text : "";

  const meta = document.createElement("div");
  meta.className = "bubble__meta";

  const confidence = payload && payload.confidence;
  if (confidence === "High" || confidence === "Medium" || confidence === "Low") {
    const badge = document.createElement("span");
    const cls = confidence.toLowerCase();
    badge.className = `badge badge--${cls}`;
    badge.textContent = `Confidence: ${confidence}`;
    meta.appendChild(badge);
  }

  const citations = payload && Array.isArray(payload.citations) ? payload.citations : [];
  if (citations.length > 0) {
    const citeWrap = document.createElement("div");
    citeWrap.className = "citations";

    const citeTitle = document.createElement("div");
    citeTitle.className = "citations__title";
    citeTitle.textContent = "Citations";

    const ul = document.createElement("ul");
    ul.className = "citations__list";
    citations.forEach((c) => {
      const li = document.createElement("li");
      li.textContent = String(c);
      ul.appendChild(li);
    });

    citeWrap.appendChild(citeTitle);
    citeWrap.appendChild(ul);
    meta.appendChild(citeWrap);
  }

  const audioUrl = resolveUrl(payload && payload.audio_output_url);
  if (audioUrl) {
    const audioWrap = document.createElement("div");
    audioWrap.className = "audio-player";
    const audio = document.createElement("audio");
    audio.controls = true;
    audio.src = audioUrl;
    audioWrap.appendChild(audio);
    meta.appendChild(audioWrap);
  }

  bubble.appendChild(title);
  bubble.appendChild(body);
  if (meta.childNodes.length) bubble.appendChild(meta);

  container.appendChild(bubble);
}

function setEscalationUI(payload) {
  const banner = document.getElementById("escalationBanner");
  const reasonEl = document.getElementById("escalationReason");
  if (!banner || !reasonEl) return;

  const escalate = payload && payload.escalate === true;
  if (!escalate) {
    setHidden(banner, true);
    reasonEl.textContent = "";
    return;
  }

  const reason = payload && payload.reason;
  reasonEl.textContent = reason ? String(reason) : "No reason provided.";
  setHidden(banner, false);
}

function initFarmerChatPage() {
  const chatRoot = document.querySelector('[data-page="farmer-chat"]');
  if (!chatRoot) return;

  if (isTokenExpired()) {
    redirectToLogin();
    return;
  }

  const chatMessages = document.getElementById("chatMessages");
  const chatForm = document.getElementById("chatForm");
  const chatInput = document.getElementById("chatInput");
  const sendBtn = document.getElementById("sendBtn");

  const imageInput = document.getElementById("imageInput");
  const audioInput = document.getElementById("audioInput");
  const imageBtn = document.getElementById("imageBtn");
  const audioBtn = document.getElementById("audioBtn");
  const composerImageBtn = document.getElementById("composerImageBtn");
  const composerAudioBtn = document.getElementById("composerAudioBtn");
  const attachmentStatus = document.getElementById("attachmentStatus");

  if (!chatMessages || !chatForm || !chatInput || !sendBtn || !imageInput || !audioInput) return;

  function updateAttachmentStatus() {
    const parts = [];
    if (imageInput.files && imageInput.files[0]) parts.push(`Image: ${imageInput.files[0].name}`);
    if (audioInput.files && audioInput.files[0]) parts.push(`Audio: ${audioInput.files[0].name}`);
    if (attachmentStatus) attachmentStatus.textContent = parts.length ? parts.join(" | ") : "No attachments selected.";
  }

  updateAttachmentStatus();
  imageInput.addEventListener("change", updateAttachmentStatus);
  audioInput.addEventListener("change", updateAttachmentStatus);

  function openImagePicker() {
    imageInput.click();
  }

  function openAudioPicker() {
    audioInput.click();
  }

  if (imageBtn) imageBtn.addEventListener("click", openImagePicker);
  if (audioBtn) audioBtn.addEventListener("click", openAudioPicker);
  if (composerImageBtn) composerImageBtn.addEventListener("click", openImagePicker);
  if (composerAudioBtn) composerAudioBtn.addEventListener("click", openAudioPicker);

  document.querySelectorAll(".chip").forEach((chip) => {
    chip.addEventListener("click", () => {
      const text = chip.textContent || "";
      chatInput.value = text;
      chatInput.focus();
    });
  });

  // Add keyboard shortcuts
  document.addEventListener('keydown', (e) => {
    // Ctrl/Cmd + Enter to submit chat form
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      if (document.activeElement === chatInput && !sendBtn.disabled) {
        e.preventDefault();
        chatForm.dispatchEvent(new Event('submit'));
      }
    }
    
    // Escape to clear attachments
    if (e.key === 'Escape') {
      if (document.activeElement === chatInput) {
        imageInput.value = '';
        audioInput.value = '';
        updateAttachmentStatus();
      }
    }
  });

  chatForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    setErrorById("chatError", "");
    setEscalationUI({ escalate: false });

    if (isTokenExpired()) {
      redirectToLogin();
      return;
    }

    const text = String(chatInput.value || "").trim();
    const imageFile = imageInput.files && imageInput.files[0] ? imageInput.files[0] : null;
    const audioFile = audioInput.files && audioInput.files[0] ? audioInput.files[0] : null;

    if (!text && !imageFile && !audioFile) {
      setErrorById("chatError", "Please add text, an image, an audio file, or any combination before sending.");
      chatInput.focus();
      return;
    }

    // Disable form and show loading state
    sendBtn.disabled = true;
    const prevSendText = sendBtn.textContent;
    sendBtn.textContent = "Sending…";
    sendBtn.classList.add("loading");
    chatInput.disabled = true;
    imageBtn.disabled = true;
    audioBtn.disabled = true;
    composerImageBtn.disabled = true;
    composerAudioBtn.disabled = true;

    appendUserBubble(chatMessages, text, imageFile, audioFile);
    scrollToBottom(chatMessages);

    const formData = new FormData();
    if (text) formData.append("text", text);
    if (audioFile) formData.append("audio", audioFile);
    if (imageFile) formData.append("image", imageFile);

    const { accessToken } = getTokenInfo();
    if (!accessToken) {
      redirectToLogin();
      return;
    }

    try {
      const res = await fetch(`${API_BASE_URL}/api/v1/chat`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${accessToken}`,
        },
        body: formData,
      });

      if (res.status === 401) {
        redirectToLogin();
        return;
      }

      if (!res.ok) {
        const msg = await parseErrorMessage(res, "Chat request failed. Please try again.");
        setErrorById("chatError", msg || "Chat request failed. Please try again.");
        return;
      }

      const data = await res.json();
      setEscalationUI(data);
      appendAssistantBubble(chatMessages, data);
      scrollToBottom(chatMessages);

      chatInput.value = "";
      imageInput.value = "";
      audioInput.value = "";
      updateAttachmentStatus();
      chatInput.focus();
    } catch (error) {
      console.error("Chat error:", error);
      setErrorById("chatError", "Unable to connect to the server. Please check your internet connection and try again.");
    } finally {
      sendBtn.disabled = false;
      sendBtn.textContent = prevSendText;
      sendBtn.classList.remove("loading");
      chatInput.disabled = false;
      imageBtn.disabled = false;
      audioBtn.disabled = false;
      composerImageBtn.disabled = false;
      composerAudioBtn.disabled = false;
    }
  });
}

function markActiveNav() {
  const page = getCurrentPage();
  document.querySelectorAll(".nav__link").forEach((a) => {
    const href = (a.getAttribute("href") || "").toLowerCase();
    if (href === page) a.classList.add("is-active");
  });
}

function scrollToBottom(element) {
  if (element) {
    setTimeout(() => {
      element.scrollTop = element.scrollHeight;
    }, 100);
  }
}

function setHidden(el, hidden) {
  if (!el) return;
  el.classList.toggle("is-hidden", hidden);
}

function setErrorById(id, message) {
  const el = document.getElementById(id);
  if (!el) return;
  el.textContent = message;
  setHidden(el, !message);
}

function setError(message) {
  const errorEl = document.getElementById("loginError");
  if (!errorEl) return;
  errorEl.textContent = message;
  setHidden(errorEl, !message);
}

function getTokenInfo() {
  const accessToken = sessionStorage.getItem("access_token");
  const expiresInRaw = sessionStorage.getItem("expires_in");
  const acquiredAtRaw = sessionStorage.getItem("token_acquired_at");

  const expiresIn = expiresInRaw ? Number(expiresInRaw) : null;
  const acquiredAt = acquiredAtRaw ? Number(acquiredAtRaw) : null;

  return {
    accessToken: accessToken || null,
    expiresIn: Number.isFinite(expiresIn) ? expiresIn : null,
    acquiredAt: Number.isFinite(acquiredAt) ? acquiredAt : null,
  };
}

function isTokenExpired() {
  const { accessToken, expiresIn, acquiredAt } = getTokenInfo();
  if (!accessToken) return true;
  if (expiresIn == null || acquiredAt == null) return false;
  const now = Date.now();
  const expiresAt = acquiredAt + expiresIn * 1000;
  return now >= expiresAt;
}

function redirectToLogin() {
  sessionStorage.removeItem("access_token");
  sessionStorage.removeItem("role");
  sessionStorage.removeItem("expires_in");
  sessionStorage.removeItem("token_acquired_at");
  window.location.href = "login.html";
}

async function parseErrorMessage(res, fallbackMessage) {
  const contentType = res.headers.get("content-type") || "";
  try {
    if (contentType.includes("application/json")) {
      const data = await res.json();
      if (typeof data === "string") return data;
      if (data && typeof data.detail === "string") return data.detail;
      if (data && data.error && typeof data.error.message === "string") return data.error.message;
      if (data && typeof data.message === "string") return data.message;
      if (data && typeof data.error === "string") return data.error;
      return fallbackMessage || "Request failed.";
    }
    const text = await res.text();
    return text || fallbackMessage || "Request failed.";
  } catch {
    return fallbackMessage || "Request failed.";
  }
}

function initOfficerDashboardPage() {
  const dashboardRoot = document.querySelector('[data-page="officer-dashboard"]');
  if (!dashboardRoot) return;

  if (isTokenExpired()) {
    redirectToLogin();
    return;
  }

  const role = sessionStorage.getItem("role");
  const blockedEl = document.getElementById("officerBlocked");
  const errorEl = document.getElementById("officerDashboardError");
  const infoEl = document.getElementById("officerDashboardInfo");
  const listEl = document.getElementById("escalationsList");
  const refreshBtn = document.getElementById("refreshEscalationsBtn");

  const pendingEl = document.getElementById("pendingEscalations");
  const resolvedEl = document.getElementById("resolvedEscalations");

  let resolvedCount = 0;
  let pendingCount = 0;
  function setResolvedCount(next) {
    resolvedCount = next;
    if (resolvedEl) resolvedEl.textContent = String(resolvedCount);
  }

  function setPendingCount(next) {
    pendingCount = next;
    if (pendingEl) pendingEl.textContent = String(pendingCount);
  }

  function setInfo(message) {
    if (!infoEl) return;
    infoEl.textContent = message;
    setHidden(infoEl, !message);
  }

  function setDashError(message) {
    setErrorById("officerDashboardError", message);
  }

  function setBlocked(message) {
    if (!blockedEl) return;
    blockedEl.textContent = message;
    setHidden(blockedEl, !message);
  }

  function clearList() {
    if (!listEl) return;
    listEl.innerHTML = "";
  }

  function disableDashboard(disabled) {
    if (refreshBtn) refreshBtn.disabled = disabled;
    if (listEl) listEl.style.display = disabled ? "none" : "";
  }

  if (role !== "officer") {
    setBlocked("Officer-only access. Please sign in with an officer account.");
    disableDashboard(true);
    return;
  }

  setBlocked("");
  disableDashboard(false);
  setDashError("");
  setInfo("");
  setResolvedCount(0);

  function pickOriginalQuery(context) {
    const inputs = context && typeof context === "object" ? context.inputs : null;
    const text = inputs && typeof inputs.text === "string" ? inputs.text : "";
    const transcript = inputs && typeof inputs.audio_transcript === "string" ? inputs.audio_transcript : "";
    const imageName = inputs && typeof inputs.image_filename === "string" ? inputs.image_filename : "";

    const parts = [];
    if (text) parts.push({ label: "Text", value: text });
    if (transcript) parts.push({ label: "Audio transcript", value: transcript });
    if (imageName) parts.push({ label: "Image", value: imageName });
    return parts;
  }

  function el(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text != null) node.textContent = text;
    return node;
  }

  function renderEscalationCard(record) {
    const card = el("article", "case-card");
    card.dataset.id = record.id;

    const header = el("div", "case-card__header");
    header.appendChild(el("div", "case-card__title", `Case ${record.id}`));
    const created = record.created_at ? String(record.created_at) : "";
    header.appendChild(el("div", "muted", created));
    card.appendChild(header);

    const grid = el("div", "case-grid");

    const queryBox = el("section", "case-box");
    queryBox.appendChild(el("div", "case-box__title", "Original farmer query"));
    const queryParts = pickOriginalQuery(record.context);
    if (queryParts.length === 0) {
      queryBox.appendChild(el("div", "muted", "No text/audio/image details available."));
    } else {
      queryParts.forEach((p) => {
        const row = el("div", "case-row");
        row.appendChild(el("div", "case-row__label", p.label));
        row.appendChild(el("div", "case-row__value", p.value));
        queryBox.appendChild(row);
      });
    }
    grid.appendChild(queryBox);

    const aiBox = el("section", "case-box");
    aiBox.appendChild(el("div", "case-box__title", "AI response"));
    const aiText = record.ai_response && record.ai_response.response_text ? record.ai_response.response_text : "";
    aiBox.appendChild(el("div", "case-box__body", aiText));
    const reason = record.ai_response && record.ai_response.reason ? record.ai_response.reason : "";
    if (reason) {
      const reasonRow = el("div", "case-row");
      reasonRow.appendChild(el("div", "case-row__label", "Escalation reason"));
      reasonRow.appendChild(el("div", "case-row__value", reason));
      aiBox.appendChild(reasonRow);
    }
    grid.appendChild(aiBox);

    const respondBox = el("section", "case-box");
    respondBox.appendChild(el("div", "case-box__title", "Officer response"));

    const confirm = el("div", "case-confirm is-hidden");
    confirm.textContent = "Response submitted. Marked as resolved.";

    const form = el("form", "form");
    form.dataset.caseId = record.id;

    const field = el("label", "field");
    field.appendChild(el("span", "field__label", "Verified advisory"));
    const textarea = document.createElement("textarea");
    textarea.className = "input";
    textarea.rows = 5;
    textarea.required = true;
    textarea.name = "response_text";
    textarea.placeholder = "Write a clear, actionable response for the farmer…";
    field.appendChild(textarea);
    form.appendChild(field);

    const citeField = el("label", "field");
    citeField.appendChild(el("span", "field__label", "Citations (optional, one per line)"));
    const citeArea = document.createElement("textarea");
    citeArea.className = "input";
    citeArea.rows = 3;
    citeArea.name = "citations";
    citeArea.placeholder = "e.g. https://example.com/source";
    citeField.appendChild(citeArea);
    form.appendChild(citeField);

    const actions = el("div", "actions");
    const submitBtn = el("button", "btn btn--primary", "Submit response");
    submitBtn.type = "submit";
    actions.appendChild(submitBtn);
    form.appendChild(actions);

    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      setDashError("");
      setInfo("");

      if (isTokenExpired()) {
        redirectToLogin();
        return;
      }

      const { accessToken } = getTokenInfo();
      if (!accessToken) {
        redirectToLogin();
        return;
      }

      const responseText = String(textarea.value || "").trim();
      if (!responseText) {
        setDashError("Response text is required. Please provide a verified advisory for the farmer.");
        textarea.focus();
        return;
      }

      const citationsRaw = String(citeArea.value || "");
      const citations = citationsRaw
        .split("\n")
        .map((s) => s.trim())
        .filter(Boolean);

      // Disable form and show loading state
      submitBtn.disabled = true;
      const prev = submitBtn.textContent;
      submitBtn.textContent = "Submitting…";
      textarea.disabled = true;
      citeArea.disabled = true;

      try {
        const res = await fetch(`${API_BASE_URL}/api/v1/officer/respond/${record.id}`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${accessToken}`,
          },
          body: JSON.stringify({
            response_text: responseText,
            citations,
          }),
        });

        if (res.status === 401) {
          redirectToLogin();
          return;
        }

        if (res.status === 403) {
          setBlocked("Officer-only access. Please sign in with an officer account.");
          disableDashboard(true);
          return;
        }

        if (!res.ok) {
          const msg = await parseErrorMessage(res, "Failed to submit officer response. Please try again.");
          setDashError(msg);
          // Re-enable form on error
          submitBtn.disabled = false;
          submitBtn.textContent = prev;
          textarea.disabled = false;
          citeArea.disabled = false;
          textarea.focus();
          return;
        }

        setHidden(confirm, false);
        textarea.disabled = true;
        citeArea.disabled = true;
        submitBtn.disabled = true;

        setResolvedCount(resolvedCount + 1);
        setPendingCount(Math.max(0, pendingCount - 1));
        setInfo("Officer response submitted successfully. Case marked as resolved.");

        const statusPill = el("span", "pill pill--green", "Resolved");
        header.appendChild(statusPill);

        // Remove card after a short delay to show success state
        setTimeout(() => {
          card.remove();
        }, 1500);
      } catch (error) {
        console.error("Officer response error:", error);
        setDashError("Unable to connect to the server. Please check your internet connection and try again.");
        // Re-enable form on error
        submitBtn.disabled = false;
        submitBtn.textContent = prev;
        textarea.disabled = false;
        citeArea.disabled = false;
        textarea.focus();
      }
    });

    respondBox.appendChild(confirm);
    respondBox.appendChild(form);
    grid.appendChild(respondBox);

    card.appendChild(grid);
    return card;
  }

  async function loadEscalations() {
    setDashError("");
    setInfo("");
    clearList();

    if (isTokenExpired()) {
      redirectToLogin();
      return;
    }

    const { accessToken } = getTokenInfo();
    if (!accessToken) {
      redirectToLogin();
      return;
    }

    // Show loading state
    if (refreshBtn) {
      refreshBtn.disabled = true;
      refreshBtn.textContent = "Loading…";
    }
    
    // Show loading indicator in the list area
    if (listEl) {
      listEl.innerHTML = "";
      const loadingItem = el("div", "muted", "Loading escalations…");
      loadingItem.style.textAlign = "center";
      loadingItem.style.padding = "2rem";
      listEl.appendChild(loadingItem);
    }

    try {
      const res = await fetch(`${API_BASE_URL}/api/v1/officer/escalations`, {
        headers: {
          Authorization: `Bearer ${accessToken}`,
        },
      });

      if (res.status === 401) {
        redirectToLogin();
        return;
      }

      if (res.status === 403) {
        setBlocked("Officer-only access. Please sign in with an officer account.");
        disableDashboard(true);
        return;
      }

      if (!res.ok) {
        const msg = await parseErrorMessage(res, "Failed to load escalations. Please try again.");
        setDashError(msg);
        if (listEl) {
          listEl.innerHTML = "";
          listEl.appendChild(el("div", "muted", "Failed to load escalations. Please try refreshing."));
        }
        return;
      }

      const items = await res.json();
      const list = Array.isArray(items) ? items : [];
      const unresolved = list.filter((it) => !it.verified_response);
      setPendingCount(unresolved.length);

      if (!listEl) return;
      
      listEl.innerHTML = "";
      
      if (unresolved.length === 0) {
        listEl.appendChild(el("div", "muted", "No pending escalations. All cases have been resolved."));
        setInfo("All caught up! No pending escalations to review.");
        return;
      }

      unresolved.forEach((rec) => {
        listEl.appendChild(renderEscalationCard(rec));
      });
      
      if (unresolved.length === 1) {
        setInfo(`Found 1 pending escalation to review.`);
      } else {
        setInfo(`Found ${unresolved.length} pending escalations to review.`);
      }
    } catch (error) {
      console.error("Load escalations error:", error);
      setDashError("Unable to connect to the server. Please check your internet connection and try again.");
      if (listEl) {
        listEl.innerHTML = "";
        listEl.appendChild(el("div", "muted", "Unable to load escalations. Please check your connection and try again."));
      }
    } finally {
      if (refreshBtn) {
        refreshBtn.disabled = false;
        refreshBtn.textContent = "Refresh";
      }
    }
  }

  if (refreshBtn) refreshBtn.addEventListener("click", loadEscalations);
  loadEscalations();
}

function initLoginPage() {
  const form = document.getElementById("loginForm");
  const usernameInput = document.getElementById("usernameInput");
  const passwordInput = document.getElementById("passwordInput");
  const loginBtn = document.getElementById("loginBtn");
  const authPanel = document.querySelector(".auth__panel");
  if (!form || !usernameInput || !passwordInput || !loginBtn) return;

  setError("");

  // Add keyboard shortcuts for login
  document.addEventListener('keydown', (e) => {
    // Enter to submit login form when in password field
    if (e.key === 'Enter' && document.activeElement === passwordInput) {
      e.preventDefault();
      form.dispatchEvent(new Event('submit'));
    }
  });

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    setError("");

    const username = String(usernameInput.value || "").trim();
    const password = String(passwordInput.value || "");

    if (!username || !password) {
      setError("Please enter both username and password.");
      usernameInput.focus();
      return;
    }

    // Disable form and show loading state
    loginBtn.disabled = true;
    const prevText = loginBtn.textContent;
    loginBtn.textContent = "Signing in…";
    usernameInput.disabled = true;
    passwordInput.disabled = true;
    
    if (authPanel) authPanel.classList.add("loading");

    try {
      const res = await fetch(`${API_BASE_URL}/auth/login`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          username,
          password,
        }),
      });

      if (!res.ok) {
        const msg = await parseErrorMessage(res, "Login failed. Please check your credentials and try again.");
        setError(msg);
        passwordInput.focus();
        passwordInput.select();
        return;
      }

      const data = await res.json();

      const token = data && data.access_token;
      const role = data && data.role;

      if (typeof token !== "string" || !token) {
        setError("Login succeeded but no access token was returned. Please try again.");
        return;
      }

      if (role !== "farmer" && role !== "officer") {
        setError("Login succeeded but returned an unknown role. Please contact support.");
        return;
      }

      sessionStorage.setItem("access_token", token);
      sessionStorage.setItem("role", role);
      if (typeof data.expires_in === "number") {
        sessionStorage.setItem("expires_in", String(data.expires_in));
      }
      sessionStorage.setItem("token_acquired_at", String(Date.now()));

      window.location.href = role === "officer" ? "officer-dashboard.html" : "farmer-chat.html";
    } catch (error) {
      console.error("Login error:", error);
      setError("Unable to connect to the server. Please check your internet connection and try again.");
      usernameInput.focus();
    } finally {
      loginBtn.disabled = false;
      loginBtn.textContent = prevText;
      usernameInput.disabled = false;
      passwordInput.disabled = false;
      if (authPanel) authPanel.classList.remove("loading");
    }
  });
}

function init() {
  markActiveNav();
  initLoginPage();
  initFarmerChatPage();
  initOfficerDashboardPage();
}

document.addEventListener("DOMContentLoaded", init);
