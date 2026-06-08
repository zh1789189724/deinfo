package com.deinfo.controller;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.deinfo.entity.GlobalContent;
import com.deinfo.service.GlobalContentService;
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

import static org.mockito.ArgumentMatchers.*;
import static org.mockito.BDDMockito.given;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@ExtendWith(MockitoExtension.class)
class GlobalControllerTest {

    private MockMvc mockMvc;

    @Mock
    private GlobalContentService globalContentService;

    private ObjectMapper objectMapper;

    @BeforeEach
    void setUp() {
        objectMapper = new ObjectMapper();
        mockMvc = MockMvcBuilders.standaloneSetup(new GlobalController(globalContentService)).build();
    }

    private GlobalContent createGlobal(Long id, String title) {
        GlobalContent gc = new GlobalContent();
        gc.setId(id);
        gc.setTitle(title);
        gc.setTitleCn("中文标题");
        gc.setOriginalLang("en");
        gc.setCategory("技术");
        gc.setStatus("active");
        return gc;
    }

    @Test
    @DisplayName("GET /api/global 返回 PageResult")
    void listGlobal() throws Exception {
        Page<GlobalContent> page = new Page<>(1, 20);
        page.setRecords(List.of(createGlobal(1L, "Original Title")));
        page.setTotal(1);
        given(globalContentService.page(any(Page.class), any(QueryWrapper.class))).willReturn(page);

        mockMvc.perform(get("/api/global"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.data.length()").value(1))
                .andExpect(jsonPath("$.total").value(1));
    }

    @Test
    @DisplayName("GET /api/global/1 存在时返回（有中文翻译时替换）")
    void getGlobalById_found() throws Exception {
        GlobalContent gc = createGlobal(1L, "Original");
        gc.setContentCn("中文内容");
        given(globalContentService.getById(1L)).willReturn(gc);

        mockMvc.perform(get("/api/global/1"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.title").value("中文标题"));
    }

    @Test
    @DisplayName("GET /api/global/2 无中文翻译时保留原文")
    void getGlobalById_noTranslation() throws Exception {
        GlobalContent gc = createGlobal(2L, "English Only Article");
        gc.setTitleCn(null);
        gc.setContentCn(null);
        gc.setSummaryCn(null);
        given(globalContentService.getById(2L)).willReturn(gc);

        mockMvc.perform(get("/api/global/2"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.title").value("English Only Article"));
    }

    @Test
    @DisplayName("GET /api/global/999 不存在返回 404")
    void getGlobalById_notFound() throws Exception {
        given(globalContentService.getById(999L)).willReturn(null);

        mockMvc.perform(get("/api/global/999"))
                .andExpect(status().isNotFound());
    }

    @Test
    @DisplayName("POST /api/global 创建")
    void createGlobal() throws Exception {
        GlobalContent gc = createGlobal(null, "New");

        mockMvc.perform(post("/api/global")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(gc)))
                .andExpect(status().isOk());
    }

    @Test
    @DisplayName("GET /api/global/top 返回高分列表")
    void topGlobal() throws Exception {
        given(globalContentService.list(any(QueryWrapper.class)))
                .willReturn(List.of(createGlobal(1L, "Top1"), createGlobal(2L, "Top2")));

        mockMvc.perform(get("/api/global/top"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.length()").value(2));
    }
}
