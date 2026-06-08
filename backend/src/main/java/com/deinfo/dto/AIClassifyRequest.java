package com.deinfo.dto;

import lombok.Data;

@Data
public class AIClassifyRequest {
    private String content;
    private String context;  // "deal", "global", "opportunity", etc.
}
