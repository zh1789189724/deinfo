package com.deinfo.controller;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.deinfo.dto.PageResult;
import com.deinfo.entity.Deal;
import com.deinfo.service.DealService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/deals")
@RequiredArgsConstructor
public class DealController {

    private final DealService dealService;

    @GetMapping
    public ResponseEntity<PageResult<Deal>> list(
            @RequestParam(required = false) String keyword,
            @RequestParam(required = false) String category,
            @RequestParam(required = false) String status,
            @RequestParam(required = false) String location,
            @RequestParam(defaultValue = "1") int page,
            @RequestParam(defaultValue = "20") int size) {
        QueryWrapper<Deal> wrapper = new QueryWrapper<>();
        if (keyword != null && !keyword.isEmpty()) {
            wrapper.like("title", keyword).or().like("summary", keyword);
        }
        if (category != null && !category.isEmpty()) {
            wrapper.eq("category", category);
        }
        if (status != null && !status.isEmpty()) {
            wrapper.eq("status", status);
        }
        if (location != null && !location.isEmpty()) {
            wrapper.eq("location", location);
        }
        wrapper.orderByDesc("created_at");
        Page<Deal> pageParam = new Page<>(page, size);
        return ResponseEntity.ok(PageResult.from(dealService.page(pageParam, wrapper)));
    }

    @GetMapping("/{id}")
    public ResponseEntity<Deal> getById(@PathVariable Long id) {
        Deal deal = dealService.getById(id);
        if (deal == null) {
            return ResponseEntity.notFound().build();
        }
        return ResponseEntity.ok(deal);
    }

    @PostMapping
    public ResponseEntity<Deal> create(@RequestBody Deal deal) {
        dealService.save(deal);
        return ResponseEntity.ok(deal);
    }

    @PutMapping("/{id}")
    public ResponseEntity<Deal> update(@PathVariable Long id, @RequestBody Deal deal) {
        deal.setId(id);
        if (!dealService.updateById(deal)) {
            return ResponseEntity.notFound().build();
        }
        return ResponseEntity.ok(deal);
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<Void> delete(@PathVariable Long id) {
        Deal deal = dealService.getById(id);
        if (deal == null) {
            return ResponseEntity.notFound().build();
        }
        dealService.removeById(id);
        return ResponseEntity.ok().build();
    }

    @GetMapping("/top")
    public ResponseEntity<List<Deal>> top(@RequestParam(defaultValue = "10") int limit) {
        QueryWrapper<Deal> wrapper = new QueryWrapper<>();
        wrapper.orderByDesc("score").last("LIMIT " + limit);
        return ResponseEntity.ok(dealService.list(wrapper));
    }
}
