import http from "k6/http";
import { check, sleep } from "k6";

export const options = {
  vus: __ENV.K6_VUS ? parseInt(__ENV.K6_VUS, 10) : 10,
  duration: __ENV.K6_DURATION || "1m",
  thresholds: {
    http_req_duration: ["p(95)<1200"],
    checks: ["rate>0.95"],
  },
};

const API_KEY = __ENV.RAG_API_KEY || "dev-astro-key";
const BASE_URL = __ENV.BASE_URL || "http://localhost:8000/v1/rag/answer";

export default function () {
  const payload = JSON.stringify({
    query: "Koç burcu için bugünkü astrolojik eğilimler nedir?",
    locale_settings: { locale: "tr-TR", language: "tr", user_level: "beginner" },
    mode_settings: { mode: "natal" },
    constraints: { max_tokens: 400, max_latency_ms: 2500 },
  });

  const res = http.post(BASE_URL, payload, {
    headers: {
      "Content-Type": "application/json",
      "X-API-Key": API_KEY,
    },
  });

  check(res, {
    "status is 200": (r) => r.status === 200,
    "contains payload.answer.general_profile": (r) =>
      !!r.json()?.payload?.answer?.general_profile,
  });

  sleep(0.3);
}

