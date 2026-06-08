package com.deinfo.service;

import com.deinfo.dto.AITranslateRequest;
import com.deinfo.dto.AITranslateResponse;
import com.deinfo.dto.AIClassifyRequest;
import com.deinfo.dto.AIClassifyResponse;
import com.deinfo.entity.GlobalContent;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Component;

import java.util.Map;

@Component
@RequiredArgsConstructor
public class GlobalService {

    private final AiService aiService;
    private final GlobalContentService globalContentService;

    public GlobalContent processAndSave(Map<String, Object> contentData) {
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
        gc.setOriginalUrl((String) contentData.get("originalUrl"));
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
