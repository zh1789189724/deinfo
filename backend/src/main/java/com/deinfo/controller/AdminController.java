package com.deinfo.controller;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.deinfo.entity.Opportunity;
import com.deinfo.entity.SubmitRecord;
import com.deinfo.service.OpportunityService;
import com.deinfo.service.SubmitRecordService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/admin")
@RequiredArgsConstructor
public class AdminController {

    private final SubmitRecordService submitRecordService;
    private final OpportunityService opportunityService;

    @GetMapping("/submissions/pending")
    public ResponseEntity<List<SubmitRecord>> listPendingSubmissions() {
        LambdaQueryWrapper<SubmitRecord> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(SubmitRecord::getStatus, "pending");
        List<SubmitRecord> pending = submitRecordService.list(wrapper);
        return ResponseEntity.ok(pending);
    }

    @PutMapping("/submissions/{id}/approve")
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

    @PutMapping("/submissions/{id}/reject")
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

    @GetMapping("/opportunities/pending")
    public ResponseEntity<List<Opportunity>> listPendingOpportunities() {
        LambdaQueryWrapper<Opportunity> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(Opportunity::getStatus, "pending");
        List<Opportunity> pending = opportunityService.list(wrapper);
        return ResponseEntity.ok(pending);
    }

    @PutMapping("/opportunities/{id}/approve")
    public ResponseEntity<Map<String, String>> approveOpportunity(@PathVariable Long id) {
        Opportunity opportunity = opportunityService.getById(id);
        if (opportunity == null) {
            return ResponseEntity.notFound().build();
        }
        opportunity.setStatus("approved");
        opportunityService.updateById(opportunity);
        return ResponseEntity.ok(Map.of("message", "Opportunity approved"));
    }

    @PutMapping("/opportunities/{id}/reject")
    public ResponseEntity<Map<String, String>> rejectOpportunity(@PathVariable Long id) {
        Opportunity opportunity = opportunityService.getById(id);
        if (opportunity == null) {
            return ResponseEntity.notFound().build();
        }
        opportunity.setStatus("rejected");
        opportunityService.updateById(opportunity);
        return ResponseEntity.ok(Map.of("message", "Opportunity rejected"));
    }

    public static class RejectRequest {
        private String reason;

        public RejectRequest() {
        }

        public RejectRequest(String reason) {
            this.reason = reason;
        }

        public String getReason() {
            return reason;
        }

        public void setReason(String reason) {
            this.reason = reason;
        }
    }
}
