package com.deinfo.controller;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.deinfo.entity.Opportunity;
import com.deinfo.service.OpportunityService;
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
class OpportunityControllerTest {

    private MockMvc mockMvc;

    @Mock
    private OpportunityService opportunityService;

    private ObjectMapper objectMapper;

    @BeforeEach
    void setUp() {
        objectMapper = new ObjectMapper();
        mockMvc = MockMvcBuilders.standaloneSetup(new OpportunityController(opportunityService)).build();
    }

    private Opportunity createOpp(Long id, String title) {
        Opportunity opp = new Opportunity();
        opp.setId(id);
        opp.setTitle(title);
        opp.setCategory("投资");
        opp.setStatus("进行中");
        return opp;
    }

    @Test
    @DisplayName("GET /api/opportunities 返回 PageResult")
    void list() throws Exception {
        Page<Opportunity> page = new Page<>(1, 20);
        page.setRecords(List.of(createOpp(1L, "测试投资机会")));
        page.setTotal(1);
        given(opportunityService.page(any(Page.class), any(QueryWrapper.class))).willReturn(page);

        mockMvc.perform(get("/api/opportunities"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.data.length()").value(1))
                .andExpect(jsonPath("$.total").value(1));
    }

    @Test
    @DisplayName("GET /api/opportunities/1 存在时返回")
    void getById_found() throws Exception {
        given(opportunityService.getById(1L)).willReturn(createOpp(1L, "投资机会"));

        mockMvc.perform(get("/api/opportunities/1"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.title").value("投资机会"));
    }

    @Test
    @DisplayName("GET /api/opportunities/999 不存在返回 404")
    void getById_notFound() throws Exception {
        given(opportunityService.getById(999L)).willReturn(null);

        mockMvc.perform(get("/api/opportunities/999"))
                .andExpect(status().isNotFound());
    }

    @Test
    @DisplayName("POST /api/opportunities 创建")
    void create() throws Exception {
        Opportunity opp = createOpp(null, "新机会");

        mockMvc.perform(post("/api/opportunities")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(opp)))
                .andExpect(status().isOk());
    }
}
