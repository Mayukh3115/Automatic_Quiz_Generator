document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("quiz-form");
  const topicInput = document.getElementById("topic");
  const statusEl = document.getElementById("status");
  const generateBtn = document.getElementById("generate-btn");
  const quizContainer = document.getElementById("quiz-container");
  const downloadBtn = document.getElementById("download-pdf-btn");
  const quizMeta = document.getElementById("quiz-meta");
  const scoreArea = document.getElementById("score-area");
  const scoreText = document.getElementById("score-text");

  let currentQuiz = [];
  let answeredCount = 0;
  let correctCount = 0;

  function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== "") {
      const cookies = document.cookie.split(";");
      for (let cookie of cookies) {
        cookie = cookie.trim();
        if (cookie.startsWith(name + "=")) {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }

  const csrftoken = getCookie("csrftoken");

  async function authFetch(url, options) {
    const res = await fetch(url, options);
    if (res.status === 401 || res.status === 403) {
      window.location.href = "/signup/?next=/";
      return null;
    }
    return res;
  }

  function setStatus(text, busy = false) {
    statusEl.querySelector("span:last-child").textContent = text;
    generateBtn.disabled = busy;
    statusEl.querySelector(".status-dot").style.background =
      busy ? "#fbbf24" : "#4ade80";
  }

  function getOptionLetter(i) {
    return String.fromCharCode(65 + i);
  }

  function resetScore() {
    answeredCount = 0;
    correctCount = 0;
    scoreArea.style.display = "none";
  }

  function updateScore(isCorrect) {
    answeredCount++;
    if (isCorrect) correctCount++;
    scoreText.textContent = `${correctCount} / ${currentQuiz.length}`;
    scoreArea.style.display = "block";
  }

  function renderQuiz(quizData, topic, difficulty) {
    currentQuiz = quizData;
    quizContainer.innerHTML = "";

    quizMeta.innerHTML = `
      <div class="meta-pill">Topic: ${topic}</div>
      <div class="meta-pill">Questions: ${quizData.length}</div>
      <div class="meta-pill">Difficulty: ${difficulty}</div>
    `;

    resetScore();
    downloadBtn.disabled = false;

    quizData.forEach((q, idx) => {
      const card = document.createElement("div");
      card.className = "question-card";

      const optionsHTML = q.options
        .map(
          (opt, i) => `
          <button class="option-btn" data-correct="${opt === q.correct_answer}">
            <div class="option-label">${getOptionLetter(i)}</div>
            <div class="option-text">${opt}</div>
          </button>
        `
        )
        .join("");

      card.innerHTML = `
        <div class="question-header">Question ${idx + 1}</div>
        <div class="question-text">${q.question}</div>
        <div class="options">${optionsHTML}</div>
        <div class="feedback" style="display:none;"></div>
      `;

      quizContainer.appendChild(card);
    });

    quizContainer.querySelectorAll(".option-btn").forEach(btn => {
      btn.addEventListener("click", () => {
        const card = btn.closest(".question-card");

        if (card.dataset.answered === "true") return;

        card.dataset.answered = "true";
        const correct = btn.dataset.correct === "true";
        updateScore(correct);

        card.querySelectorAll(".option-btn").forEach(b => {
          b.disabled = true;
          b.style.pointerEvents = "none";
          b.classList.remove("selected", "correct", "incorrect");
        });

        btn.classList.add("selected", correct ? "correct" : "incorrect");

        const fb = card.querySelector(".feedback");
        fb.style.display = "flex";
        fb.className = "feedback " + (correct ? "correct" : "incorrect");
        fb.innerHTML = correct
          ? `<span class="feedback-dot correct"></span> Correct! 🎉`
          : `<span class="feedback-dot incorrect"></span> Incorrect`;
      });
    });
  }

  form.addEventListener("submit", async e => {
    e.preventDefault();

    const topic = topicInput.value.trim();
    const num_ques = document.getElementById("num_ques").value;
    const difficulty = document.getElementById("difficulty").value;

    setStatus("Generating…", true);

    try {
      const res = await authFetch("/generate_quiz/", {
        method: "POST",
        credentials: "same-origin",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrftoken
        },
        body: JSON.stringify({ topic, num_ques, difficulty })
      });

      if (!res) return;

      const data = await res.json();
      renderQuiz(data.quiz, topic, difficulty);
      setStatus("Ready");
    } catch {
      setStatus("Error");
    }
  });

  downloadBtn.addEventListener("click", async () => {
    if (!currentQuiz.length) return;

    const res = await authFetch("/download_quiz_pdf/", {
      method: "POST",
      credentials: "same-origin",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": csrftoken
      },
      body: JSON.stringify({
        topic: topicInput.value || "Quiz",
        quiz: currentQuiz
      })
    });

    if (!res) return;

    const blob = await res.blob();
    const url = URL.createObjectURL(blob);

    const a = document.createElement("a");
    a.href = url;
    a.download = "quiz.pdf";
    a.click();

    URL.revokeObjectURL(url);
  });
});