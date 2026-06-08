package com.deinfo.controller;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.deinfo.dto.PageResult;
import com.deinfo.entity.Opportunity;
import com.deinfo.service.OpportunityService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/opportunities")
public class OpportunityController {

    private final OpportunityService opportunityService;

    public OpportunityController(OpportunityService opportunityService) {
        this.opportunityService = opportunityService;
    }

    @GetMapping
    public ResponseEntity<PageResult<Opportunity>> list(
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
        Page<Opportunity> pageParam = new Page<>(page, size);
        return ResponseEntity.ok(PageResult.from(opportunityService.page(pageParam, wrapper)));
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
