package com.deinfo.service;

import com.deinfo.config.DeepSeekConfig;
import com.deinfo.dto.AIClassifyRequest;
import com.deinfo.dto.AIClassifyResponse;
import com.deinfo.dto.AITranslateRequest;
import com.deinfo.dto.AITranslateResponse;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.web.reactive.function.client.WebClient;

import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.TimeUnit;

/**
 * AI 智能评估服务
 *
 * 对接 DeepSeek API，提供内容分类、打分、摘要、翻译功能。
 * 内置重试、缓存、降级机制。
 *
 * 参考需求文档「模块 D：AI 智能评估系统」
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class AiService {

    private final DeepSeekConfig deepSeekConfig;
    private final WebClient webClient;
    private final ObjectMapper objectMapper;

    // ── 缓存 ─────────────────────────────────────────
    private final Map<String, AIClassifyResponse> classifyCache = new ConcurrentHashMap<>();
    private final Map<String, AITranslateResponse> translateCache = new ConcurrentHashMap<>();

    // ── 重试配置 ─────────────────────────────────────
    private static final int MAX_RETRIES = 3;
    private static final long BASE_DELAY_MS = 1000;

    // ── DeepSeek 响应模型（内部用）──────────────────
    private record DeepSeekResponse(List<Choice> choices) {
        private record Choice(Message message) {}
        private record Message(String content) {}
    }

    // ── 分类内容模型（从 message.content JSON 中解析）───
    private record ClassifyContent(String category, List<String> tags, String summary, Integer score) {}

    // ── 翻译内容模型 ─────────────────────────────────
    private record TranslateContent(String titleCn, String contentCn, String summaryCn) {}

    // ═════════════════════════════════════════════════
    // 公开方法
    // ═════════════════════════════════════════════════

    /**
     * AI 分类：对内容进行分类、打标签、评分、摘要
     *
     * @param request 包含 content 和 context
     * @return AIClassifyResponse（失败时返回降级默认值）
     */
    public AIClassifyResponse classify(AIClassifyRequest request) {
        String cacheKey = buildClassifyCacheKey(request);
        AIClassifyResponse cached = classifyCache.get(cacheKey);
        if (cached != null) {
            log.debug("[AI分类] 缓存命中: content={}", truncate(request.getContent(), 50));
            return cached;
        }

        String systemPrompt = switch (request.getContext() != null ? request.getContext() : "") {
            case "deal" -> "你是一个优惠信息分析助手。分析内容并返回JSON: {\"category\": \"优惠券/折扣/政府补贴/其他\", \"tags\": [\"标签\"], \"summary\": \"50字以内摘要\", \"score\": 评分0-100}";
            case "global" -> "你是一个海外信息分析助手。分析内容并返回JSON: {\"category\": \"工具/创业/行业/政策/趋势\", \"tags\": [\"标签\"], \"summary\": \"50字以内摘要\", \"score\": 评分0-100}";
            case "opportunity" -> "你是一个投资机会分析助手。分析内容并返回JSON: {\"category\": \"投资/租房/兼职/政策\", \"tags\": [\"标签\"], \"summary\": \"50字以内摘要\", \"score\": 评分0-100}";
            default -> "你是一个信息分类助手。分析内容并返回JSON: {\"category\": \"分类\", \"tags\": [\"标签\"], \"summary\": \"50字以内摘要\", \"score\": 评分0-100}";
        };

        String rawResponse = callDeepSeekApi(systemPrompt, request.getContent(), 1000);

        AIClassifyResponse result = parseClassifyResponse(rawResponse, request.getContent());
        classifyCache.put(cacheKey, result);
        log.info("[AI分类] 完成: category={}, score={}, content={}",
                result.getCategory(), result.getScore(), truncate(request.getContent(), 50));
        return result;
    }

    /**
     * AI 翻译：将内容翻译为目标语言
     *
     * @param request 包含 content、targetLang、style
     * @return AITranslateResponse（失败时返回降级默认值）
     */
    public AITranslateResponse translate(AITranslateRequest request) {
        String cacheKey = buildTranslateCacheKey(request);
        AITranslateResponse cached = translateCache.get(cacheKey);
        if (cached != null) {
            log.debug("[AI翻译] 缓存命中: content={}", truncate(request.getContent(), 50));
            return cached;
        }

        String lang = request.getTargetLang() != null ? request.getTargetLang() : "zh";
        String systemPrompt = "你是一个专业翻译助手。请将以下文本翻译为" + lang
                + "。返回JSON格式: {\"titleCn\": \"翻译标题\", \"contentCn\": \"翻译内容\", \"summaryCn\": \"翻译摘要\"}。不要返回其他内容。";

        String rawResponse = callDeepSeekApi(systemPrompt, request.getContent(), 4000);

        AITranslateResponse result = parseTranslateResponse(rawResponse, request.getContent());
        translateCache.put(cacheKey, result);
        log.info("[AI翻译] 完成: content={}", truncate(request.getContent(), 50));
        return result;
    }

    // ═════════════════════════════════════════════════
    // API 调用
    // ═════════════════════════════════════════════════

    /**
     * 调用 DeepSeek API（带指数退避重试）
     *
     * @param systemPrompt 系统提示词
     * @param userContent  用户内容
     * @param maxTokens    最大 token 数
     * @return API 响应的原始 JSON 字符串，失败时返回 null
     */
    String callDeepSeekApi(String systemPrompt, String userContent, int maxTokens) {
        Map<String, Object> body = Map.of(
            "model", "deepseek-chat",
            "messages", List.of(
                Map.of("role", "system", "content", systemPrompt),
                Map.of("role", "user", "content", userContent)
            ),
            "max_tokens", maxTokens
        );

        Exception lastException = null;

        for (int attempt = 1; attempt <= MAX_RETRIES; attempt++) {
            try {
                String result = webClient.post()
                    .uri(deepSeekConfig.getApiUrl())
                    .header("Authorization", "Bearer " + deepSeekConfig.getApiKey())
                    .header("Content-Type", "application/json")
                    .bodyValue(body)
                    .retrieve()
                    .bodyToMono(String.class)
                    .block();

                if (result != null && !result.isBlank()) {
                    return result;
                }
                lastException = new RuntimeException("API 返回空响应");
            } catch (Exception e) {
                lastException = e;
                if (attempt < MAX_RETRIES) {
                    long delay = BASE_DELAY_MS * (long) Math.pow(2, attempt - 1);
                    log.warn("[DeepSeek API] 第{}/{}次调用失败: {}，{}ms后重试",
                            attempt, MAX_RETRIES, e.getMessage(), delay);
                    try {
                        TimeUnit.MILLISECONDS.sleep(delay);
                    } catch (InterruptedException ie) {
                        Thread.currentThread().interrupt();
                        break;
                    }
                } else {
                    log.error("[DeepSeek API] {}次重试全部失败: {}", MAX_RETRIES, e.getMessage());
                }
            }
        }
        return null;
    }

    // ═════════════════════════════════════════════════
    // 响应解析
    // ═════════════════════════════════════════════════

    /**
     * 解析分类 API 响应
     *
     * @param rawResponse   DeepSeek API 原始响应（可能为 null）
     * @param originalContent 原始内容（用于降级默认值）
     * @return AIClassifyResponse
     */
    AIClassifyResponse parseClassifyResponse(String rawResponse, String originalContent) {
        if (rawResponse == null) {
            return defaultClassification(originalContent);
        }

        try {
            DeepSeekResponse outer = objectMapper.readValue(rawResponse, DeepSeekResponse.class);
            if (outer.choices() == null || outer.choices().isEmpty()) {
                log.warn("[AI分类] API 返回空 choices，使用降级值");
                return defaultClassification(originalContent);
            }

            String contentJson = outer.choices().get(0).message().content();
            if (contentJson == null || contentJson.isBlank()) {
                log.warn("[AI分类] API 返回空 content，使用降级值");
                return defaultClassification(originalContent);
            }

            // 清理可能的 markdown 代码块包裹
            contentJson = contentJson.trim();
            if (contentJson.startsWith("```")) {
                contentJson = contentJson.replaceAll("```[a-zA-Z]*\\n?", "").replaceAll("```", "");
            }

            ClassifyContent parsed = objectMapper.readValue(contentJson, ClassifyContent.class);

            AIClassifyResponse response = new AIClassifyResponse();
            response.setCategory(parsed.category() != null ? parsed.category() : "other");
            response.setTags(parsed.tags() != null ? parsed.tags() : List.of());
            response.setSummary(parsed.summary() != null ? parsed.summary() : truncate(originalContent, 100));
            response.setScore(parsed.score() != null ? Math.max(0, Math.min(100, parsed.score())) : 50);

            return response;
        } catch (Exception e) {
            log.error("[AI分类] JSON 解析失败: {}", e.getMessage());
            return defaultClassification(originalContent);
        }
    }

    /**
     * 解析翻译 API 响应
     *
     * @param rawResponse   DeepSeek API 原始响应（可能为 null）
     * @param originalContent 原始内容（用于降级默认值）
     * @return AITranslateResponse
     */
    AITranslateResponse parseTranslateResponse(String rawResponse, String originalContent) {
        if (rawResponse == null) {
            return defaultTranslation(originalContent);
        }

        try {
            DeepSeekResponse outer = objectMapper.readValue(rawResponse, DeepSeekResponse.class);
            if (outer.choices() == null || outer.choices().isEmpty()) {
                log.warn("[AI翻译] API 返回空 choices，使用降级值");
                return defaultTranslation(originalContent);
            }

            String contentJson = outer.choices().get(0).message().content();
            if (contentJson == null || contentJson.isBlank()) {
                log.warn("[AI翻译] API 返回空 content，使用降级值");
                return defaultTranslation(originalContent);
            }

            // 清理可能的 markdown 代码块包裹
            contentJson = contentJson.trim();
            if (contentJson.startsWith("```")) {
                contentJson = contentJson.replaceAll("```[a-zA-Z]*\\n?", "").replaceAll("```", "");
            }

            TranslateContent parsed = objectMapper.readValue(contentJson, TranslateContent.class);

            AITranslateResponse response = new AITranslateResponse();
            response.setTitleCn(parsed.titleCn() != null ? parsed.titleCn() : truncate(originalContent, 100));
            response.setContentCn(parsed.contentCn() != null ? parsed.contentCn() : originalContent);
            response.setSummaryCn(parsed.summaryCn() != null ? parsed.summaryCn() : truncate(originalContent, 200));

            return response;
        } catch (Exception e) {
            log.error("[AI翻译] JSON 解析失败: {}", e.getMessage());
            return defaultTranslation(originalContent);
        }
    }

    // ═════════════════════════════════════════════════
    // 降级默认值
    // ═════════════════════════════════════════════════

    private AIClassifyResponse defaultClassification(String content) {
        AIClassifyResponse r = new AIClassifyResponse();
        r.setCategory("other");
        r.setTags(List.of());
        r.setSummary(content != null && content.length() > 200 ? content.substring(0, 200) : content);
        r.setScore(50);
        return r;
    }

    private AITranslateResponse defaultTranslation(String content) {
        AITranslateResponse r = new AITranslateResponse();
        String truncated = content != null && content.length() > 100 ? content.substring(0, 100) : content;
        r.setTitleCn(truncated);
        r.setContentCn(content);
        r.setSummaryCn(content != null && content.length() > 200 ? content.substring(0, 200) : content);
        return r;
    }

    // ═════════════════════════════════════════════════
    // 缓存管理
    // ═════════════════════════════════════════════════

    private String buildClassifyCacheKey(AIClassifyRequest request) {
        return request.getContent() + "::" + (request.getContext() != null ? request.getContext() : "");
    }

    private String buildTranslateCacheKey(AITranslateRequest request) {
        return request.getContent() + "::" + (request.getTargetLang() != null ? request.getTargetLang() : "zh");
    }

    /**
     * 清空所有缓存（管理员手动触发时使用）
     */
    public void clearCache() {
        classifyCache.clear();
        translateCache.clear();
        log.info("[AI] 缓存已清空");
    }

    // ═════════════════════════════════════════════════
    // 工具方法
    // ═════════════════════════════════════════════════

    private String truncate(String text, int maxLen) {
        if (text == null) return "";
        return text.length() <= maxLen ? text : text.substring(0, maxLen) + "...";
    }
}
