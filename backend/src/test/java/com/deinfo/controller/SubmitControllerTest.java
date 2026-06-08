package com.deinfo.controller;

import com.deinfo.entity.SubmitRecord;
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

import static org.mockito.BDDMockito.given;
import static org.mockito.ArgumentMatchers.any;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@ExtendWith(MockitoExtension.class)
class SubmitControllerTest {

    private MockMvc mockMvc;

    @Mock
    private SubmitRecordService submitRecordService;

    private ObjectMapper objectMapper;

    @BeforeEach
    void setUp() {
        objectMapper = new ObjectMapper();
        mockMvc = MockMvcBuilders.standaloneSetup(new SubmitController(submitRecordService)).build();
    }

    private SubmitRecord createRecord(Long id, String title) {
        SubmitRecord record = new SubmitRecord();
        record.setId(id);
        record.setTitle(title);
        record.setCategory("deal");
        record.setStatus("pending");
        return record;
    }

    @Test
    @DisplayName("POST /api/submit 提交成功返回记录")
    void submit_success() throws Exception {
        SubmitRecord record = createRecord(null, "新爆料");
        given(submitRecordService.save(any())).willReturn(true);

        mockMvc.perform(post("/api/submit")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(record)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.title").value("新爆料"))
                .andExpect(jsonPath("$.userId").value(1));
    }

    @Test
    @DisplayName("GET /api/submit/1 存在时返回")
    void getById_found() throws Exception {
        given(submitRecordService.getById(1L)).willReturn(createRecord(1L, "爆料详情"));

        mockMvc.perform(get("/api/submit/1"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.title").value("爆料详情"));
    }

    @Test
    @DisplayName("GET /api/submit/999 不存在返回 404")
    void getById_notFound() throws Exception {
        given(submitRecordService.getById(999L)).willReturn(null);

        mockMvc.perform(get("/api/submit/999"))
                .andExpect(status().isNotFound());
    }
}
