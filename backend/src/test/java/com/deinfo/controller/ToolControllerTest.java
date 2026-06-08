package com.deinfo.controller;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.deinfo.entity.ToolItem;
import com.deinfo.service.ToolItemService;
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
class ToolControllerTest {

    private MockMvc mockMvc;

    @Mock
    private ToolItemService toolItemService;

    private ObjectMapper objectMapper;

    @BeforeEach
    void setUp() {
        objectMapper = new ObjectMapper();
        mockMvc = MockMvcBuilders.standaloneSetup(new ToolController(toolItemService)).build();
    }

    private ToolItem createTool(Long id, String name) {
        ToolItem tool = new ToolItem();
        tool.setId(id);
        tool.setName(name);
        tool.setUrl("https://example.com");
        tool.setTag("效率");
        return tool;
    }

    @Test
    @DisplayName("GET /api/tools 返回 PageResult")
    void list() throws Exception {
        Page<ToolItem> page = new Page<>(1, 20);
        page.setRecords(List.of(createTool(1L, "Test Tool")));
        page.setTotal(1);
        given(toolItemService.page(any(Page.class), any(QueryWrapper.class))).willReturn(page);

        mockMvc.perform(get("/api/tools"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.data.length()").value(1))
                .andExpect(jsonPath("$.total").value(1));
    }

    @Test
    @DisplayName("GET /api/tools/1 存在时返回")
    void getById_found() throws Exception {
        given(toolItemService.getById(1L)).willReturn(createTool(1L, "Test Tool"));

        mockMvc.perform(get("/api/tools/1"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.name").value("Test Tool"));
    }

    @Test
    @DisplayName("GET /api/tools/999 不存在返回 404")
    void getById_notFound() throws Exception {
        given(toolItemService.getById(999L)).willReturn(null);

        mockMvc.perform(get("/api/tools/999"))
                .andExpect(status().isNotFound());
    }

    @Test
    @DisplayName("POST /api/tools 创建")
    void create() throws Exception {
        ToolItem tool = createTool(null, "New Tool");

        mockMvc.perform(post("/api/tools")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(tool)))
                .andExpect(status().isOk());
    }
}
