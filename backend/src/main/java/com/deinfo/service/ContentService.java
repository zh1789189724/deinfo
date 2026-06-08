package com.deinfo.service;

import com.deinfo.dto.AIClassifyRequest;
import com.deinfo.dto.AIClassifyResponse;
import com.deinfo.entity.Deal;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Component;

import java.util.Map;

@Component
@RequiredArgsConstructor
public class ContentService {

    private final AiService aiService;
    private final DealService dealService;

    public Deal processAndSave(Map<String, Object> dealData) {
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
        deal.setOriginalUrl((String) dealData.get("originalUrl"));

        dealService.save(deal);
        return deal;
    }
}
