package com.deinfo.service;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.deinfo.dto.AIClassifyRequest;
import com.deinfo.dto.AIClassifyResponse;
import com.deinfo.entity.Deal;
import lombok.RequiredArgsConstructor;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;

import java.util.Map;

@Component
@RequiredArgsConstructor
public class ContentService {

    private static final Logger log = LoggerFactory.getLogger(ContentService.class);

    private final AiService aiService;
    private final DealService dealService;

    public Deal processAndSave(Map<String, Object> dealData) {
        // ── 去重：检查 original_url 是否已存在 ──
        String originalUrl = (String) dealData.get("originalUrl");
        if (originalUrl != null && !originalUrl.isBlank()) {
            LambdaQueryWrapper<Deal> wrapper = new LambdaQueryWrapper<>();
            wrapper.eq(Deal::getOriginalUrl, originalUrl);
            if (dealService.count(wrapper) > 0) {
                log.info("[去重] 跳过已存在的国内内容: {}", originalUrl);
                return null;
            }
        }

        String title = (String) dealData.get("title");
        String description = (String) dealData.get("description");
        String combined = title + "\n" + description;

        AIClassifyRequest classifyReq = new AIClassifyRequest();
        classifyReq.setContent(combined);
        classifyReq.setContext("deal");
        AIClassifyResponse ai = aiService.classify(classifyReq);

        Deal deal = new Deal();
        deal.setTitle(title);
        deal.setDescription(description);
        deal.setSummary(ai.getSummary());
        deal.setCategory(ai.getCategory());
        deal.setTag(String.join(",", ai.getTags()));
        deal.setScore(ai.getScore());
        deal.setStatus("active");
        deal.setOriginalUrl(originalUrl);

        dealService.save(deal);
        return deal;
    }
}
