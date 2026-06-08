package com.deinfo.controller;

import com.baomidou.mybatisplus.core.conditions.Wrapper;
import com.deinfo.dto.StatsResponse;
import com.deinfo.entity.SubmitRecord;
import com.deinfo.service.OpportunityService;
import com.deinfo.service.SubmitRecordService;
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
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@ExtendWith(MockitoExtension.class)
class AdminControllerTest {

    private MockMvc mockMvc;

    @Mock
    private SubmitRecordService submitRecordService;
    @Mock
    private OpportunityService opportunityService;

    private ObjectMapper objectMapper;

    @BeforeEach
    void setUp() {
        objectMapper = new ObjectMapper();
        mockMvc = MockMvcBuilders.standaloneSetup(new AdminController(submitRecordService, opportunityService)).build();
    }

    @Test
    @DisplayName("GET /api/admin/pending 返回待审核列表")
    void pending() throws Exception {
        SubmitRecord r = new SubmitRecord();
        r.setId(1L);
        r.setTitle("待审核");
        given(submitRecordService.list(any(Wrapper.class))).willReturn(List.of(r));

        mockMvc.perform(get("/api/admin/pending"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.length()").value(1));
    }

    @Test
    @DisplayName("PUT /api/admin/submit/1/approve 通过审核")
    void approveSubmission() throws Exception {
        SubmitRecord r = new SubmitRecord();
        r.setId(1L);
        r.setStatus("pending");
        given(submitRecordService.getById(1L)).willReturn(r);

        mockMvc.perform(put("/api/admin/submit/1/approve"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.message").value("Submission approved"));
    }

    @Test
    @DisplayName("PUT /api/admin/submit/1/reject 拒绝审核")
    void rejectSubmission() throws Exception {
        SubmitRecord r = new SubmitRecord();
        r.setId(1L);
        r.setStatus("pending");
        given(submitRecordService.getById(1L)).willReturn(r);

        Map<String, String> body = Map.of("reason", "内容质量不佳");

        mockMvc.perform(put("/api/admin/submit/1/reject")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(body)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.message").value("Submission rejected"));
    }

    @Test
    @DisplayName("GET /api/admin/stats 返回统计")
    void stats() throws Exception {
        given(submitRecordService.count(any())).willReturn(5L);

        mockMvc.perform(get("/api/admin/stats"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.pending").isNumber());
    }
}
