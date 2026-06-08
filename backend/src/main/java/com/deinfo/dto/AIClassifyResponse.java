package com.deinfo.dto;

import lombok.Data;
import java.util.List;

@Data
public class AIClassifyResponse {
    private String category;
    private List<String> tags;
    private String summary;
    private Integer score;
}
