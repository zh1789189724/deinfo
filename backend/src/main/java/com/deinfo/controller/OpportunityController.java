package com.deinfo.controller;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.deinfo.entity.Opportunity;
import com.deinfo.service.OpportunityService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/opportunities")
public class OpportunityController {

    private final OpportunityService opportunityService;

    public OpportunityController(OpportunityService opportunityService) {
        this.opportunityService = opportunityService;
    }

    @GetMapping
    public ResponseEntity<List<Opportunity>> list(
            @RequestParam(required = false) String category,
            @RequestParam(required = false) String status,
            @RequestParam(defaultValue = "1") int page,
            @RequestParam(defaultValue = "20") int size) {
        QueryWrapper<Opportunity> wrapper = new QueryWrapper<>();
        if (category != null && !category.isEmpty()) {
            wrapper.eq("category", category);
        }
        if (status != null && !status.isEmpty()) {
            wrapper.eq("status", status);
        }
        wrapper.orderByDesc("created_at");
        List<Opportunity> all = opportunityService.list(wrapper);
        int start = Math.min((page - 1) * size, all.size());
        int end = Math.min(start + size, all.size());
        return ResponseEntity.ok(all.subList(start, end));
    }

    @GetMapping("/{id}")
    public ResponseEntity<Opportunity> getById(@PathVariable Long id) {
        Opportunity opportunity = opportunityService.getById(id);
        if (opportunity == null) {
            return ResponseEntity.notFound().build();
        }
        return ResponseEntity.ok(opportunity);
    }

    @PostMapping
    public ResponseEntity<Opportunity> create(@RequestBody Opportunity opportunity) {
        opportunityService.save(opportunity);
        return ResponseEntity.ok(opportunity);
    }

    @PutMapping("/{id}")
    public ResponseEntity<Opportunity> update(@PathVariable Long id, @RequestBody Opportunity updated) {
        Opportunity existing = opportunityService.getById(id);
        if (existing == null) {
            return ResponseEntity.notFound().build();
        }
        if ("approved".equals(existing.getStatus()) || "rejected".equals(existing.getStatus())) {
            return ResponseEntity.badRequest().build();
        }
        updated.setId(id);
        opportunityService.updateById(updated);
        return ResponseEntity.ok(updated);
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<Void> delete(@PathVariable Long id) {
        Opportunity existing = opportunityService.getById(id);
        if (existing == null) {
            return ResponseEntity.notFound().build();
        }
        opportunityService.removeById(id);
        return ResponseEntity.ok().build();
    }
}
