package com.deinfo.dto;

import lombok.Data;

@Data
public class AITranslateRequest {
    private String content;
    private String targetLang;
    private String style;
}
