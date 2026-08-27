const API_URL = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000").replace(/\/$/, "");

async function request(path, options) {
  const response = await fetch(`${API_URL}${path}`, options);
  if (!response.ok) {
    let detail;
    try { detail = (await response.json()).detail; } catch { detail = null; }
    throw new Error(detail?.message || "The server could not complete this request.");
  }
  return response.json();
}

export function absoluteAssetUrl(path) {
  return path.startsWith("http") ? path : `${API_URL}${path}`;
}

export function createAssessment(questionPaper, answerSheet) {
  const body = new FormData();
  body.append("question_paper", questionPaper);
  body.append("answer_sheet", answerSheet);
  return request("/api/assessments", { method: "POST", body });
}

export const getJob = (id) => request(`/api/assessments/${id}`, { cache: "no-store" });
export const getResult = (id) => request(`/api/assessments/${id}/result`, { cache: "no-store" });
