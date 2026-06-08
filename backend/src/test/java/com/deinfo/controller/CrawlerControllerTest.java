package com.deinfo.controller;

import com.deinfo.entity.Deal;
import com.deinfo.entity.GlobalContent;
import com.deinfo.service.ContentService;
import com.deinfo.service.GlobalService;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;

import java.util.List;
import java.util.Map;

import static org.mockito.ArgumentMatchers.*;
import static org.mockito.BDDMockito.given;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@ExtendWith(MockitoExtension.class)
class CrawlerControllerTest {

    private MockMvc mockMvc;

    @Mock
    private ContentService contentService;
    @Mock
    private GlobalService globalService;

    private ObjectMapper objectMapper;

    @BeforeEach
    void setUp() {
        objectMapper = new ObjectMapper();
        mockMvc = MockMvcBuilders.standaloneSetup(new CrawlerController(contentService, globalService)).build();
    }

    @Test
    @DisplayName("POST /api/crawler/push 国内源推送成功")
    void push_domestic() throws Exception {
        Deal deal = new Deal();
        deal.setId(1L);
        deal.setTitle("测试优惠");
        given(contentService.processAndSave(any())).willReturn(deal);

        Map<String, Object> payload = Map.of(
            "sourceType", "domestic",
            "sourceName", "wechat_chengdu",
            "content", Map.of("title", "测试优惠", "content", "内容")
        );

        mockMvc.perform(post("/api/crawler/push")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(payload)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.type").value("domestic"))
                .andExpect(jsonPath("$.deal.title").value("测试优惠"));
    }

    @Test
    @DisplayName("POST /api/crawler/push 海外源推送成功")
    void push_overseas() throws Exception {
        GlobalContent gc = new GlobalContent();
        gc.setId(1L);
        gc.setTitle("Original");
        given(globalService.processAndSave(any())).willReturn(gc);

        Map<String, Object> payload = Map.of(
            "sourceType", "overseas",
            "sourceName", "producthunt",
            "content", Map.of("title", "Original", "content", "Desc")
        );

        mockMvc.perform(post("/api/crawler/push")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(payload)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.type").value("overseas"))
                .andExpect(jsonPath("$.content.title").value("Original"));
    }

    @Test
    @DisplayName("POST /api/crawler/push 缺少 content 返回 400")
    void push_missingContent() throws Exception {
        Map<String, Object> payload = Map.of("sourceType", "domestic");

        mockMvc.perform(post("/api/crawler/push")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(payload)))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.error").value("content is required"));
    }
}
