document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById('quiz-form');
  const topicInput = document.getElementById('topic');  
  const statusEl = document.getElementById('status');
  const generateBtn = document.getElementById('generate-btn');
  const quizContainer = document.getElementById('quiz-container');
  const showAnswersBtn = document.getElementById('show-answers-btn');
  const quizMeta = document.getElementById('quiz-meta');
  const scoreArea = document.getElementById('score-area');
  const scoreText = document.getElementById('score-text');

  let currentQuiz = [];
  let answeredCount = 0;
  let correctCount = 0;

  function setStatus(text, busy = false) {
    statusEl.querySelector('span:last-child').textContent = text;
    generateBtn.disabled = busy;
    statusEl.querySelector('.status-dot').style.background = busy ? '#fbbf24' : '#4ade80';
  }

  function getOptionLetter(i) {
    return String.fromCharCode(65 + i);
  }

  function resetScore() {
    answeredCount = correctCount = 0;
    scoreArea.style.display = 'none';
  }

  function updateScore(isCorrect) {
    answeredCount++;
    if (isCorrect) correctCount++;
    scoreText.textContent = `${correctCount} / ${currentQuiz.length}`;
    scoreArea.style.display = 'block';
  }

  function renderQuiz(quizData, topic, num, difficulty) {
    currentQuiz = quizData;
    quizContainer.innerHTML = "";
    if (!quizData.length) return;

    quizMeta.innerHTML = `
      <div class="meta-pill">Topic: ${topic}</div>
      <div class="meta-pill">Questions: ${quizData.length}</div>
      <div class="meta-pill">Difficulty: ${difficulty}</div>
    `;

    resetScore();
    showAnswersBtn.disabled = false;

    quizData.forEach((q, idx) => {
      const card = document.createElement("div");
      card.className = "question-card";
      card.dataset.index = idx;

      const optionsHTML = q.options.map((opt, i) => `
        <button class="option-btn" data-correct="${opt === q.correct_answer}">
          <div class="option-label">${getOptionLetter(i)}</div>
          <div class="option-text">${opt}</div>
        </button>
      `).join("");

      card.innerHTML = `
        <div class="question-header">
          <div class="question-index">Question ${idx+1}</div>
        </div>
        <div class="question-text">${q.question}</div>
        <div class="options">${optionsHTML}</div>
        <div class="feedback" style="display:none;"></div>
      `;

      quizContainer.appendChild(card);
    });

    quizContainer.querySelectorAll(".option-btn").forEach(btn => {
      btn.addEventListener("click", () => {
        const card = btn.closest(".question-card");
        const already = card.dataset.answered === "true";
        const correct = btn.dataset.correct === "true";

        if (!already) {
          card.dataset.answered = "true";
          updateScore(correct);
        }

        card.querySelectorAll(".option-btn").forEach(b => b.classList.remove("selected", "correct", "incorrect"));
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

  showAnswersBtn.addEventListener("click", () => {
    document.querySelectorAll(".question-card").forEach(card => {
      card.querySelectorAll(".option-btn").forEach(btn => {
        if (btn.dataset.correct === "true") btn.classList.add("reveal-correct");
      });
    });
  });

  form.addEventListener("submit", async e => {
    e.preventDefault();

    const topic = topicInput.value.trim();
    const num_ques = document.getElementById("num_ques").value;
    const difficulty = document.getElementById("difficulty").value;

    if (!topic) return alert("Please enter a topic.");

    setStatus("Generating…", true);

    const res = await fetch("/generate_quiz/", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({ topic, num_ques, difficulty })
    });

    setStatus("Ready", false);

    if (!res.ok) {
      quizContainer.innerHTML = `<p class="error">Error: ${res.status}</p>`;
      return;
    }

    const data = await res.json();
    renderQuiz(data.quiz, topic, num_ques, difficulty);
  });
});