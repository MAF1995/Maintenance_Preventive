async function fetchJson(path) {
  const response = await fetch(path);
  if (!response.ok) {
    throw new Error(`HTTP ${response.status} on ${path}`);
  }
  return await response.json();
}

function formatMetric(value) {
  if (typeof value === "number") {
    return value.toFixed(3);
  }
  return String(value);
}

function renderFeatureImportance(items) {
  const container = document.getElementById("feature-importance");
  container.innerHTML = "";
  const maxImportance = Math.max(...items.map((item) => item.importance), 0.0001);

  items.forEach((item) => {
    const wrapper = document.createElement("div");
    const label = document.createElement("div");
    label.className = "bar-item-label";
    label.innerHTML = `<span>${item.feature}</span><strong>${item.importance.toFixed(3)}</strong>`;

    const track = document.createElement("div");
    track.className = "bar-item-track";
    const fill = document.createElement("div");
    fill.className = "bar-item-fill";
    fill.style.width = `${(item.importance / maxImportance) * 100}%`;
    track.appendChild(fill);

    wrapper.appendChild(label);
    wrapper.appendChild(track);
    container.appendChild(wrapper);
  });
}

function renderConfusionMatrix(confusion) {
  const container = document.getElementById("confusion-grid");
  container.innerHTML = "";

  const mapping = [
    ["Vrais négatifs", confusion.true_negative],
    ["Faux positifs", confusion.false_positive],
    ["Faux négatifs", confusion.false_negative],
    ["Vrais positifs", confusion.true_positive],
  ];

  mapping.forEach(([label, value]) => {
    const cell = document.createElement("div");
    cell.className = "confusion-cell";
    cell.innerHTML = `<span>${label}</span><strong>${value}</strong>`;
    container.appendChild(cell);
  });
}

function renderPredictionSample(rows) {
  const tbody = document.querySelector("#sample-table tbody");
  tbody.innerHTML = "";

  rows.forEach((row) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${row.cycle_id}</td>
      <td>${row.valve_pct}</td>
      <td>${row.is_valve_optimal}</td>
      <td>${row.predicted_label}</td>
      <td>${Number(row.predicted_probability).toFixed(3)}</td>
    `;
    tbody.appendChild(tr);
  });
}

function renderPredictionResult(prediction) {
  const container = document.getElementById("prediction-result");
  container.innerHTML = `
    <div class="prediction-card"><strong>Classe prédite</strong><div>${prediction.predicted_class_name}</div></div>
    <div class="prediction-card"><strong>Probabilité</strong><div>${Number(prediction.predicted_probability).toFixed(3)}</div></div>
    <div class="prediction-card"><strong>Label binaire</strong><div>${prediction.predicted_label}</div></div>
    <div class="prediction-card"><strong>Valve réelle</strong><div>${prediction.actual_valve_pct}</div></div>
  `;
}

async function bootstrapUi() {
  try {
    const [{ metrics, confusion_matrix }, featureImportance, sample] = await Promise.all([
      fetchJson("/model/metrics"),
      fetchJson("/model/feature-importance?limit=8"),
      fetchJson("/model/test-sample?limit=20"),
    ]);

    document.getElementById("metric-accuracy").textContent = formatMetric(metrics.accuracy);
    document.getElementById("metric-f1").textContent = formatMetric(metrics.f1);
    document.getElementById("metric-roc").textContent = formatMetric(metrics.roc_auc);
    document.getElementById("metric-test-cycles").textContent = metrics.test_cycles;

    renderFeatureImportance(featureImportance);
    renderConfusionMatrix(confusion_matrix);
    renderPredictionSample(sample);

    if (sample.length > 0) {
      document.getElementById("cycle-id").value = sample[0].cycle_id;
    }
  } catch (error) {
    document.querySelector(".page-shell").innerHTML = `
      <section class="panel">
        <h1>Impossible de charger l'interface</h1>
        <p>Vérifiez que l'API locale ou Docker est bien démarrée avec les endpoints <code>/model/metrics</code> et <code>/predict/{cycle_id}</code>.</p>
        <pre>${error.message}</pre>
      </section>
    `;
  }
}

document.getElementById("predict-button").addEventListener("click", async () => {
  const cycleId = document.getElementById("cycle-id").value;
  try {
    const prediction = await fetchJson(`/predict/${cycleId}`);
    renderPredictionResult(prediction);
  } catch (error) {
    document.getElementById("prediction-result").innerHTML = `<div class="prediction-card">Erreur : ${error.message}</div>`;
  }
});

bootstrapUi();
