document.addEventListener('DOMContentLoaded', () => {
    const navLinks = document.querySelectorAll('.nav-links a');
    const viewContainer = document.getElementById('view-container');

    // Define views
    const views = {
        dashboard: {
            title: 'Dashboard & News',
            desc: 'Latest updates from Official Malls and the EC Industry.',
            render: renderDashboard
        },
        manuals: {
            title: 'Knowledge Base',
            desc: 'Foundational EC knowledge, mall specifics, and operations.',
            render: renderManuals
        },
        quizzes: {
            title: 'Skill Quizzes',
            desc: 'Test your understanding of EC concepts and technical knowledge.',
            render: renderQuizzes
        },
        cases: {
            title: 'Case Studies',
            desc: 'Practice problem-solving and logical thinking in real-world scenarios.',
            render: renderCases
        }
    };

    // Navigation Logic
    function setActiveNav(selectedViewId) {
        navLinks.forEach(link => {
            if (link.dataset.view === selectedViewId) {
                link.classList.add('active');
            } else {
                link.classList.remove('active');
            }
        });
    }

    function loadView(viewId) {
        const view = views[viewId];
        if (!view) return;

        setActiveNav(viewId);

        // Render Shell
        viewContainer.innerHTML = `
            <div class="view-header">
                <h1>${view.title}</h1>
                <p>${view.desc}</p>
            </div>
            <div id="${viewId}-content" class="view-content">
                <div class="loading">Loading content...</div>
            </div>
        `;

        // Execute specific view render logic
        view.render(document.getElementById(`${viewId}-content`));
    }

    // Event Listeners for Nav
    navLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const viewId = e.target.dataset.view;
            loadView(viewId);
        });
    });

    // State
    let quizzesData = [];
    let casesData = [];
    let manualsData = [];
    let newsData = [];

    const THEMES = ["All", "EC業界知識", "EC運営基礎知識", "楽天市場", "ヤフーショッピング", "Amazon", "Qoo10", "TikTokshop"];

    // Helper to render theme filter buttons
    function renderThemeFilters(container, currentTheme, onSelect) {
        let html = '';
        THEMES.forEach(theme => {
            const isActive = theme === currentTheme;
            html += `<button class="theme-pill ${isActive ? 'active' : ''}" data-theme="${theme}" style="padding: 0.5rem 1rem; border-radius: 999px; border: 1px solid var(--border); background: ${isActive ? 'var(--primary)' : 'white'}; color: ${isActive ? 'white' : 'var(--text-main)'}; cursor: pointer; font-size: 0.85rem; transition: all 0.2s; white-space: nowrap;">${theme}</button>`;
        });
        container.innerHTML = html;

        container.querySelectorAll('.theme-pill').forEach(btn => {
            btn.addEventListener('click', (e) => {
                onSelect(e.target.dataset.theme);
            });
        });
    }

    // Render logic functions
    async function loadJsonData(url, stateArray) {
        try {
            const res = await fetch(url);
            stateArray.length = 0; // Clear array
            const data = await res.json();
            stateArray.push(...data);
            return true;
        } catch (e) {
            console.error("Failed to load " + url, e);
            return false;
        }
    }

    async function renderDashboard(container) {
        if (newsData.length === 0) {
            await loadJsonData('/data/news.json', newsData);
        }

        if (newsData.length === 0) {
            container.innerHTML = `<p>No news or updates found at this time.</p>`;
            return;
        }

        // Sort news by date descending (assuming format YYYY-MM-DD)
        const sortedNews = [...newsData].sort((a, b) => (new Date(b.date)) - (new Date(a.date)));

        let html = '<div class="news-grid" style="display: grid; gap: 1.5rem;">';
        sortedNews.forEach(n => {
            html += `
                <div class="card news-card" style="border-left: 4px solid var(--primary); padding: 1.5rem; background: var(--bg-main); border-radius: 0.5rem; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                    <div style="font-size: 0.85rem; color: var(--text-muted); margin-bottom: 0.5rem;">${n.date}</div>
                    <h3 style="margin-bottom: 0.75rem; color: var(--text-main); font-size: 1.25rem;">${n.title}</h3>
                    <p style="margin-bottom: 1rem; color: var(--text-muted); line-height: 1.5;">${n.summary}</p>
                    <a href="${n.original_source}" target="_blank" class="source-citation">Original Source &rarr;</a>
                </div>
            `;
        });
        html += '</div>';

        container.innerHTML = html;
    }

    async function renderManuals(container) {
        if (manualsData.length === 0) {
            await loadJsonData('/data/manuals.json', manualsData);
        }

        let currentTheme = 'All';
        container.innerHTML = `
            <div class="theme-filter-container" style="margin-bottom: 2rem; display: flex; gap: 0.5rem; flex-wrap: wrap;"></div>
            <div class="data-list-container"></div>
        `;

        const filterContainer = container.querySelector('.theme-filter-container');
        const listContainer = container.querySelector('.data-list-container');

        function updateList() {
            const filteredData = currentTheme === 'All' ? manualsData : manualsData.filter(m => m.theme === currentTheme);
            if (filteredData.length === 0) {
                listContainer.innerHTML = `<p>No manuals found for this theme.</p>`;
                return;
            }

            let html = '';
            filteredData.forEach(man => {
                const contentFormatted = man.content.replace(/\n### /g, '<h3>').replace(/\n- /g, '<br>• ').replace(/\n/g, '<br>');
                html += `
                    <div class="card manual-card" style="margin-bottom: 2rem; border: 1px solid var(--border); padding: 1.5rem; border-radius: 0.5rem;">
                        <h2>${man.title}</h2>
                        <div style="margin-bottom: 1rem; color: var(--text-muted); font-size: 0.875rem;">
                            <strong>テーマ:</strong> <span style="background: #E0E7FF; color: #3730A3; padding: 0.2rem 0.5rem; border-radius: 0.25rem; font-weight: bold;">${man.theme || '未指定'}</span> | <strong>カテゴリー:</strong> ${man.category}
                        </div>
                        <div class="manual-content" style="margin-bottom: 1rem;">
                            ${contentFormatted}
                        </div>
                        <a href="${man.original_source.includes('http') ? man.original_source.match(/https?:\/\/[^\s]+/) : '#'}" class="source-citation" target="_blank">
                            Source: ${man.original_source}
                        </a>
                    </div>
                `;
            });
            listContainer.innerHTML = html;
        }

        renderThemeFilters(filterContainer, currentTheme, (newTheme) => {
            currentTheme = newTheme;
            renderThemeFilters(filterContainer, currentTheme, updateList); // update pills
            updateList();
        });

        updateList();
    }

    async function renderQuizzes(container) {
        if (quizzesData.length === 0) {
            await loadJsonData('/data/quizzes.json', quizzesData);
        }

        let currentTheme = 'All';
        container.innerHTML = `
            <div class="theme-filter-container" style="margin-bottom: 2rem; display: flex; gap: 0.5rem; flex-wrap: wrap;"></div>
            <div class="data-list-container"></div>
        `;

        const filterContainer = container.querySelector('.theme-filter-container');
        const listContainer = container.querySelector('.data-list-container');

        function updateList() {
            const filteredData = currentTheme === 'All' ? quizzesData : quizzesData.filter(q => q.theme === currentTheme);
            if (filteredData.length === 0) {
                listContainer.innerHTML = `<p>No quizzes available for this theme.</p>`;
                return;
            }

            let html = '';
            filteredData.forEach((q, index) => {
                html += `
                    <div class="card quiz-card" style="margin-bottom: 2rem; border: 1px solid var(--border); padding: 1.5rem; border-radius: 0.5rem;" id="quiz-block-${index}">
                        <div style="margin-bottom: 0.5rem;"><span style="background: #E0E7FF; color: #3730A3; padding: 0.2rem 0.5rem; border-radius: 0.25rem; font-size: 0.8rem; font-weight: bold;">${q.theme || '未指定'}</span></div>
                        <h3 style="margin-bottom: 1rem;">Q${index + 1}: ${q.question}</h3>
                        <div class="options" style="display: flex; flex-direction: column; gap: 0.5rem; margin-bottom: 1rem;">
                            ${q.options.map((opt, i) => `
                                <button class="quiz-option-btn" data-qindex="${index}" data-optindex="${i}" style="padding: 0.75rem; text-align: left; border: 1px solid var(--border); background: white; border-radius: 0.25rem; cursor: pointer;">
                                    ${i + 1}. ${opt}
                                </button>
                            `).join('')}
                        </div>
                        <div class="quiz-result" id="quiz-result-${index}" style="display: none; padding: 1rem; background: #F3F4F6; border-radius: 0.25rem;">
                            <!-- Result injected here -->
                        </div>
                    </div>
                `;
            });
            listContainer.innerHTML = html;

            // Attach quiz logic
            listContainer.querySelectorAll('.quiz-option-btn').forEach(btn => {
                btn.addEventListener('click', (e) => {
                    const qIndex = parseInt(e.target.dataset.qindex);
                    const optIndex = parseInt(e.target.dataset.optindex);
                    const quiz = filteredData[qIndex];
                    const isCorrect = optIndex === quiz.correct_answer;

                    const resultDiv = listContainer.querySelector(`#quiz-result-${qIndex}`);
                    resultDiv.style.display = 'block';
                    resultDiv.style.backgroundColor = isCorrect ? '#ecfdf5' : '#fef2f2';
                    resultDiv.style.border = `1px solid ${isCorrect ? '#34d399' : '#fca5a5'}`;

                    resultDiv.innerHTML = `
                         <h4 style="color: ${isCorrect ? '#065f46' : '#991b1b'}; margin-bottom: 0.5rem;">
                            ${isCorrect ? '✅ 正解！' : '❌ 不正解...'}
                        </h4>
                        <p style="font-size:0.95rem; line-height: 1.6;"><strong>解説:</strong> ${quiz.explanation}</p>
                        <a href="${quiz.original_source}" target="_blank" class="source-citation" style="margin-top: 1rem; display: inline-block;">Source: ${quiz.original_source}</a>
                    `;

                    // Disable options after answer
                    listContainer.querySelectorAll(`#quiz-block-${qIndex} .quiz-option-btn`).forEach(b => {
                        b.disabled = true;
                        b.style.opacity = '0.7';
                        b.style.cursor = 'default';
                        if (parseInt(b.dataset.optindex) === quiz.correct_answer) {
                            b.style.border = '2px solid #10b981';
                            b.style.backgroundColor = '#ecfdf5';
                            b.style.fontWeight = 'bold';
                        } else if (parseInt(b.dataset.optindex) === optIndex && !isCorrect) {
                            b.style.border = '2px solid #ef4444';
                            b.style.backgroundColor = '#fef2f2';
                        }
                    });
                });
            });
        }

        renderThemeFilters(filterContainer, currentTheme, (newTheme) => {
            currentTheme = newTheme;
            renderThemeFilters(filterContainer, currentTheme, updateList);
            updateList();
        });

        updateList();
    }

    async function renderCases(container) {
        if (casesData.length === 0) {
            await loadJsonData('/data/cases.json', casesData);
        }

        let currentTheme = 'All';
        container.innerHTML = `
            <div class="theme-filter-container" style="margin-bottom: 2rem; display: flex; gap: 0.5rem; flex-wrap: wrap;"></div>
            <div class="data-list-container"></div>
        `;

        const filterContainer = container.querySelector('.theme-filter-container');
        const listContainer = container.querySelector('.data-list-container');

        function updateList() {
            const filteredData = currentTheme === 'All' ? casesData : casesData.filter(c => c.theme === currentTheme);
            if (filteredData.length === 0) {
                listContainer.innerHTML = `<p>No case studies available for this theme.</p>`;
                return;
            }

            let html = '';
            filteredData.forEach((c, index) => {
                html += `
                    <div class="card case-card" style="margin-bottom: 2rem; border: 1px solid var(--border); padding: 1.5rem; border-radius: 0.5rem;" id="case-block-${index}">
                        <div style="margin-bottom: 0.5rem;"><span style="background: #E0E7FF; color: #3730A3; padding: 0.2rem 0.5rem; border-radius: 0.25rem; font-size: 0.8rem; font-weight: bold;">${c.theme || '未指定'}</span></div>
                        <h2 style="margin-bottom: 0.5rem;">${c.title}</h2>
                        <div style="margin-bottom: 1.5rem; padding: 1.25rem; background: #EEF2FF; border-left: 4px solid var(--primary); border-radius: 0 0.25rem 0.25rem 0;">
                            <strong>【シナリオ】</strong><br>
                            ${c.scenario}
                        </div>
                        <div style="margin-bottom: 1.5rem; font-size: 1.1rem; font-weight: 500;">
                            <strong>【設問】</strong><br>
                            ${c.question}
                        </div>
                        
                        <div class="user-input-area" id="case-input-area-${index}" style="margin-bottom: 1rem;">
                             <textarea style="width: 100%; min-height: 150px; padding: 1rem; border: 1px solid var(--border); border-radius: 0.25rem; font-family: inherit; font-size: 0.95rem; resize: vertical;" placeholder="ここに自身の考え（構造化された仮説やアプローチ）を論理的に書き出してください..."></textarea>
                            <button class="btn-reveal-answer" data-cindex="${index}" style="margin-top: 1rem; padding: 0.75rem 1.5rem; background: var(--primary); color: white; border: none; border-radius: 999px; cursor: pointer; font-weight: bold; transition: background 0.2s;">解答・解説を確認する</button>
                        </div>

                        <div class="case-solution-area" id="case-solution-${index}" style="display: none; margin-top: 1.5rem; padding-top: 1.5rem; border-top: 1px dashed var(--border);">
                            <h3 style="color: var(--primary); margin-bottom:0.75rem;">【模範解答・アプローチ例】</h3>
                            <div style="white-space: pre-wrap; margin-bottom: 1.5rem; background: var(--bg-main); padding: 1.25rem; border-radius: 0.5rem; line-height: 1.6;">${c.example_solution}</div>
                            
                            <h3 style="color: var(--text-main); margin-bottom:0.5rem;">【評価ルーブリック（自己採点用）】</h3>
                            <p style="color: var(--text-muted); font-size: 0.85rem; margin-bottom: 0.5rem;">以下の観点で自身の回答を満たせているか確認してください。</p>
                            <ul style="margin-bottom: 1.5rem; padding-left: 1.5rem; line-height: 1.6;">
                                ${(c.evaluation_rubric || []).map(r => `<li>${r}</li>`).join('')}
                            </ul>
                            
                            <a href="${c.original_source}" target="_blank" class="source-citation">Original Source &rarr;</a>
                        </div>
                    </div>
                `;
            });
            listContainer.innerHTML = html;

            listContainer.querySelectorAll('.btn-reveal-answer').forEach(btn => {
                btn.addEventListener('click', (e) => {
                    const cIndex = e.target.dataset.cindex;
                    const solutionDiv = listContainer.querySelector(`#case-solution-${cIndex}`);
                    solutionDiv.style.display = 'block';
                    e.target.style.display = 'none'; // Hide button

                    // Show a nice success feeling
                    solutionDiv.scrollIntoView({ behavior: 'smooth', block: 'start' });
                });
            });
        }

        renderThemeFilters(filterContainer, currentTheme, (newTheme) => {
            currentTheme = newTheme;
            renderThemeFilters(filterContainer, currentTheme, updateList);
            updateList();
        });

        updateList();
    }

    // Initialize Default View
    loadView('dashboard');
});
