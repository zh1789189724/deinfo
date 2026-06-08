package com.deinfo.controller;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.deinfo.dto.StatsResponse;
import com.deinfo.entity.Opportunity;
import com.deinfo.entity.SubmitRecord;
import com.deinfo.service.OpportunityService;
import com.deinfo.service.SubmitRecordService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.LocalTime;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/admin")
@RequiredArgsConstructor
public class AdminController {

    private final SubmitRecordService submitRecordService;
    private final OpportunityService opportunityService;

    @GetMapping("/pending")
    public ResponseEntity<List<SubmitRecord>> listPending() {
        LambdaQueryWrapper<SubmitRecord> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(SubmitRecord::getStatus, "pending");
        return ResponseEntity.ok(submitRecordService.list(wrapper));
    }

    @PutMapping("/submit/{id}/approve")
    public ResponseEntity<Map<String, String>> approveSubmission(@PathVariable Long id) {
        SubmitRecord record = submitRecordService.getById(id);
        if (record == null) {
            return ResponseEntity.notFound().build();
        }
        record.setStatus("approved");
        record.setReviewedAt(LocalDateTime.now());
        submitRecordService.updateById(record);
        return ResponseEntity.ok(Map.of("message", "Submission approved"));
    }

    @PutMapping("/submit/{id}/reject")
    public ResponseEntity<Map<String, String>> rejectSubmission(
            @PathVariable Long id,
            @RequestBody RejectRequest request) {
        SubmitRecord record = submitRecordService.getById(id);
        if (record == null) {
            return ResponseEntity.notFound().build();
        }
        record.setStatus("rejected");
        record.setRejectReason(request.getReason());
        record.setReviewedAt(LocalDateTime.now());
        submitRecordService.updateById(record);
        return ResponseEntity.ok(Map.of("message", "Submission rejected"));
    }

    @GetMapping("/stats")
    public ResponseEntity<StatsResponse> stats() {
        LambdaQueryWrapper<SubmitRecord> pendingWrapper = new LambdaQueryWrapper<>();
        pendingWrapper.eq(SubmitRecord::getStatus, "pending");
        long pending = submitRecordService.count(pendingWrapper);

        long total = submitRecordService.count();

        LambdaQueryWrapper<SubmitRecord> todayWrapper = new LambdaQueryWrapper<>();
        todayWrapper.ge(SubmitRecord::getCreatedAt, LocalDateTime.of(LocalDate.now(), LocalTime.MIDNIGHT));
        long today = submitRecordService.count(todayWrapper);

        return ResponseEntity.ok(new StatsResponse(pending, total, today));
    }

    public static class RejectRequest {
        private String reason;

        public RejectRequest() {}
        public RejectRequest(String reason) { this.reason = reason; }
        public String getReason() { return reason; }
        public void setReason(String reason) { this.reason = reason; }
    }
}
