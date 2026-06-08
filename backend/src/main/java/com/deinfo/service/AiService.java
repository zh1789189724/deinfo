package com.deinfo.service;

import com.deinfo.config.DeepSeekConfig;
import com.deinfo.dto.AIClassifyRequest;
import com.deinfo.dto.AIClassifyResponse;
import com.deinfo.dto.AITranslateRequest;
import com.deinfo.dto.AITranslateResponse;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Mono;

import java.util.*;

@Slf4j
@Service
@RequiredArgsConstructor
public class AiService {

    private final DeepSeekConfig deepSeekConfig;
    private final WebClient webClient;

    public AIClassifyResponse classify(AIClassifyRequest request) {
        Map<String, Object> body = new HashMap<>();
        body.put("model", "deepseek-chat");
        body.put("messages", List.of(
            Map.of("role", "system", "content",
                "你是一个信息分类助手。请分析内容并返回JSON格式: {\"category\": \"分类\", \"tags\": [\"标签1\", \"标签2\"], \"summary\": \"100字以内的摘要\", \"score\": 评分(0-100)}。不要返回其他内容。"),
            Map.of("role", "user", "content", request.getContent())
        ));
        body.put("max_tokens", 1000);

        String result = webClient.post()
            .uri(deepSeekConfig.getApiUrl())
            .header("Authorization", "Bearer " + deepSeekConfig.getApiKey())
            .header("Content-Type", "application/json")
            .bodyValue(body)
            .retrieve()
            .bodyToMono(String.class)
            .block();

        if (result != null && result.contains("message")) {
            String content = result;
            int idx = content.indexOf("\"content\":");
            if (idx > 0) {
                content = content.substring(idx + 10);
                content = content.replace("\"", "").replace("\\n", " ").trim();
            }
            return parseClassification(content);
        }
        return defaultClassification(request.getContent());
    }

    public AITranslateResponse translate(AITranslateRequest request) {
        Map<String, Object> body = new HashMap<>();
        body.put("model", "deepseek-chat");
        body.put("messages", List.of(
            Map.of("role", "system", "content",
                "你是一个专业翻译助手。请将以下文本翻译为" + request.getTargetLang() + "。返回JSON格式: {\"title_cn\": \"翻译标题\", \"content_cn\": \"翻译内容\", \"summary_cn\": \"翻译摘要\"}。不要返回其他内容。"),
            Map.of("role", "user", "content", request.getContent())
        ));
        body.put("max_tokens", 4000);

        String result = webClient.post()
            .uri(deepSeekConfig.getApiUrl())
            .header("Authorization", "Bearer " + deepSeekConfig.getApiKey())
            .header("Content-Type", "application/json")
            .bodyValue(body)
            .retrieve()
            .bodyToMono(String.class)
            .block();

        if (result != null && result.contains("message")) {
            String content = result;
            int idx = content.indexOf("\"content\":");
            if (idx > 0) {
                content = content.substring(idx + 10);
            }
            return parseTranslation(content);
        }
        return defaultTranslation(request.getContent());
    }

    private AIClassifyResponse parseClassification(String content) {
        AIClassifyResponse response = new AIClassifyResponse();
        try {
            int cIdx = content.indexOf("\"category\":");
            if (cIdx > 0) {
                int start = content.indexOf('"', cIdx + 11);
                int end = content.indexOf('"', start + 1);
                response.setCategory(content.substring(start + 1, end));
            }
            int tIdx = content.indexOf("\"tags\":");
            if (tIdx > 0) {
                List<String> tags = new ArrayList<>();
                int arrStart = content.indexOf('[', tIdx);
                int arrEnd = content.indexOf(']', arrStart);
                String tagsStr = content.substring(arrStart + 1, arrEnd);
                String[] items = tagsStr.split("\"");
                for (String item : items) {
                    item = item.trim().replace(",", "").replace(" ", "");
                    if (!item.isEmpty()) tags.add(item);
                }
                response.setTags(tags);
            }
            int sIdx = content.indexOf("\"summary\":");
            if (sIdx > 0) {
                int start = content.indexOf('"', sIdx + 10);
                int end = content.indexOf('"', start + 1);
                response.setSummary(content.substring(start + 1, end));
            }
            int scIdx = content.indexOf("\"score\":");
            if (scIdx > 0) {
                int start = scIdx + 8;
                while (start < content.length() && !Character.isDigit(content.charAt(start))) start++;
                int end = start;
                while (end < content.length() && Character.isDigit(content.charAt(end))) end++;
                response.setScore(Integer.parseInt(content.substring(start, end)));
            }
        } catch (Exception e) {
            log.error("Failed to parse AI classification response", e);
        }
        return response;
    }

    private AITranslateResponse parseTranslation(String content) {
        AITranslateResponse response = new AITranslateResponse();
        try {
            int tIdx = content.indexOf("\"title_cn\":");
            if (tIdx > 0) {
                int start = content.indexOf('"', tIdx + 11);
                int end = content.indexOf('"', start + 1);
                response.setTitleCn(content.substring(start + 1, end));
            }
            int cIdx = content.indexOf("\"content_cn\":");
            if (cIdx > 0) {
                int start = content.indexOf('"', cIdx + 13);
                int end = content.indexOf('"', start + 1);
                response.setContentCn(content.substring(start + 1, end));
            }
            int sIdx = content.indexOf("\"summary_cn\":");
            if (sIdx > 0) {
                int start = content.indexOf('"', sIdx + 13);
                int end = content.indexOf('"', start + 1);
                response.setSummaryCn(content.substring(start + 1, end));
            }
        } catch (Exception e) {
            log.error("Failed to parse AI translation response", e);
        }
        return response;
    }

    private AIClassifyResponse defaultClassification(String content) {
        AIClassifyResponse r = new AIClassifyResponse();
        r.setCategory("other");
        r.setTags(List.of());
        r.setSummary(content.length() > 200 ? content.substring(0, 200) : content);
        r.setScore(50);
        return r;
    }

    private AITranslateResponse defaultTranslation(String content) {
        AITranslateResponse r = new AITranslateResponse();
        r.setTitleCn(content.length() > 100 ? content.substring(0, 100) : content);
        r.setContentCn(content);
        r.setSummaryCn(content.length() > 200 ? content.substring(0, 200) : content);
        return r;
    }
}
