export function authHeaders(token) {
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export async function getJson(url, token = "") {
  const response = await fetch(url, { headers: authHeaders(token) });
  const data = await response.json();
  if (!response.ok) throw new Error(data.detail || `请求失败：${response.status}`);
  return data;
}

export async function postJson(url, payload, token = "") {
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders(token) },
    body: JSON.stringify(payload),
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.detail || `请求失败：${response.status}`);
  return data;
}
