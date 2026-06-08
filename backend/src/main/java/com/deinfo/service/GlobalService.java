package com.deinfo.service;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.deinfo.dto.AITranslateRequest;
import com.deinfo.dto.AITranslateResponse;
import com.deinfo.dto.AIClassifyRequest;
import com.deinfo.dto.AIClassifyResponse;
import com.deinfo.entity.GlobalContent;
import lombok.RequiredArgsConstructor;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;

import java.util.Map;

@Component
@RequiredArgsConstructor
public class GlobalService {

    private static final Logger log = LoggerFactory.getLogger(GlobalService.class);

    private final AiService aiService;
    private final GlobalContentService globalContentService;

    public GlobalContent processAndSave(Map<String, Object> contentData) {
        // ── 去重：检查 original_url 是否已存在 ──
        String originalUrl = (String) contentData.get("originalUrl");
        if (originalUrl != null && !originalUrl.isBlank()) {
            LambdaQueryWrapper<GlobalContent> wrapper = new LambdaQueryWrapper<>();
            wrapper.eq(GlobalContent::getOriginalUrl, originalUrl);
            if (globalContentService.count(wrapper) > 0) {
                log.info("[去重] 跳过已存在的海外内容: {}", originalUrl);
                return null;
            }
        }

        String title = (String) contentData.get("title");
        String content = (String) contentData.get("content");
        String lang = (String) contentData.get("lang");

        String combined = title + "\n" + content;
        AIClassifyRequest classifyReq = new AIClassifyRequest();
        classifyReq.setContent(combined);
        classifyReq.setContext("global");
        AIClassifyResponse classify = aiService.classify(classifyReq);

        GlobalContent gc = new GlobalContent();
        gc.setTitle(title);
        gc.setContent(content);
        gc.setOriginalLang(lang != null ? lang : "en");
        gc.setCategory(classify.getCategory());
        gc.setTag(String.join(",", classify.getTags()));
        gc.setScore(classify.getScore());
        gc.setStatus("active");
        gc.setOriginalUrl(originalUrl);
        gc.setSummary(classify.getSummary());

        AITranslateRequest translateReq = new AITranslateRequest();
        translateReq.setContent(combined);
        translateReq.setTargetLang("zh");
        translateReq.setStyle("informative");
        AITranslateResponse translate = aiService.translate(translateReq);
        gc.setTitleCn(translate.getTitleCn());
        gc.setContentCn(translate.getContentCn());
        gc.setSummaryCn(translate.getSummaryCn());

        globalContentService.save(gc);
        return gc;
    }
}
