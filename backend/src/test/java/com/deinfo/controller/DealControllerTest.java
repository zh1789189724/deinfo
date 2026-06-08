package com.deinfo.controller;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.deinfo.dto.PageResult;
import com.deinfo.entity.Deal;
import com.deinfo.service.DealService;
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

import java.math.BigDecimal;
import java.util.List;

import static org.mockito.ArgumentMatchers.*;
import static org.mockito.BDDMockito.given;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@ExtendWith(MockitoExtension.class)
class DealControllerTest {

    private MockMvc mockMvc;

    @Mock
    private DealService dealService;

    private ObjectMapper objectMapper;

    @BeforeEach
    void setUp() {
        objectMapper = new ObjectMapper();
        mockMvc = MockMvcBuilders.standaloneSetup(new DealController(dealService)).build();
    }

    private Deal createDeal(Long id, String title) {
        Deal deal = new Deal();
        deal.setId(id);
        deal.setTitle(title);
        deal.setCategory("优惠券");
        deal.setScore(85);
        deal.setPrice(new BigDecimal("25.00"));
        deal.setLocation("成都");
        deal.setStatus("active");
        return deal;
    }

    @Test
    @DisplayName("GET /api/deals 返回 PageResult")
    void listDeals() throws Exception {
        Page<Deal> page = new Page<>(1, 20);
        page.setRecords(List.of(createDeal(1L, "星巴克五折"), createDeal(2L, "政府消费券")));
        page.setTotal(2);
        given(dealService.page(any(Page.class), any(QueryWrapper.class))).willReturn(page);

        mockMvc.perform(get("/api/deals"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.data.length()").value(2))
                .andExpect(jsonPath("$.total").value(2));
    }

    @Test
    @DisplayName("GET /api/deals?keyword=xxx 支持搜索")
    void listDeals_withKeyword() throws Exception {
        Page<Deal> page = new Page<>(1, 20);
        page.setRecords(List.of(createDeal(1L, "星巴克五折")));
        page.setTotal(1);
        given(dealService.page(any(Page.class), any(QueryWrapper.class))).willReturn(page);

        mockMvc.perform(get("/api/deals?keyword=星巴克"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.total").value(1));
    }

    @Test
    @DisplayName("GET /api/deals/1 存在时返回 Deal")
    void getDealById_found() throws Exception {
        given(dealService.getById(1L)).willReturn(createDeal(1L, "星巴克五折"));

        mockMvc.perform(get("/api/deals/1"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.title").value("星巴克五折"))
                .andExpect(jsonPath("$.score").value(85));
    }

    @Test
    @DisplayName("GET /api/deals/999 不存在返回 404")
    void getDealById_notFound() throws Exception {
        given(dealService.getById(999L)).willReturn(null);

        mockMvc.perform(get("/api/deals/999"))
                .andExpect(status().isNotFound());
    }

    @Test
    @DisplayName("POST /api/deals 创建 Deal")
    void createDeal() throws Exception {
        Deal deal = createDeal(null, "新优惠");

        mockMvc.perform(post("/api/deals")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(deal)))
                .andExpect(status().isOk());
    }

    @Test
    @DisplayName("DELETE /api/deals/1 存在时返回 200")
    void deleteDeal_found() throws Exception {
        given(dealService.getById(1L)).willReturn(createDeal(1L, "测试"));

        mockMvc.perform(delete("/api/deals/1"))
                .andExpect(status().isOk());
    }

    @Test
    @DisplayName("DELETE /api/deals/999 不存在返回 404")
    void deleteDeal_notFound() throws Exception {
        given(dealService.getById(999L)).willReturn(null);

        mockMvc.perform(delete("/api/deals/999"))
                .andExpect(status().isNotFound());
    }
}
