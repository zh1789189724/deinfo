package com.deinfo.controller;

import com.deinfo.entity.SubmitRecord;
import com.deinfo.service.SubmitRecordService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/submit")
public class SubmitController {

    private final SubmitRecordService submitRecordService;

    public SubmitController(SubmitRecordService submitRecordService) {
        this.submitRecordService = submitRecordService;
    }

    @PostMapping
    public ResponseEntity<SubmitRecord> submit(@RequestBody SubmitRecord record) {
        record.setUserId(1L);
        submitRecordService.save(record);
        return ResponseEntity.ok(record);
    }

    @GetMapping("/{id}")
    public ResponseEntity<SubmitRecord> getById(@PathVariable Long id) {
        SubmitRecord record = submitRecordService.getById(id);
        if (record == null) {
            return ResponseEntity.notFound().build();
        }
        return ResponseEntity.ok(record);
    }
}
