package com.deinfo.controller;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.deinfo.dto.PageResult;
import com.deinfo.entity.GlobalContent;
import com.deinfo.service.GlobalContentService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/global")
@RequiredArgsConstructor
public class GlobalController {

    private final GlobalContentService globalContentService;

    @GetMapping
    public ResponseEntity<PageResult<GlobalContent>> list(
            @RequestParam(required = false) String category,
            @RequestParam(required = false) String status,
            @RequestParam(defaultValue = "1") int page,
            @RequestParam(defaultValue = "20") int size) {
        QueryWrapper<GlobalContent> wrapper = new QueryWrapper<>();
        if (category != null && !category.isEmpty()) {
            wrapper.eq("category", category);
        }
        if (status != null && !status.isEmpty()) {
            wrapper.eq("status", status);
        }
        wrapper.orderByDesc("created_at");
        Page<GlobalContent> pageParam = new Page<>(page, size);
        Page<GlobalContent> result = globalContentService.page(pageParam, wrapper);
        result.getRecords().forEach(this::applyChineseTranslation);
        return ResponseEntity.ok(PageResult.from(result));
    }

    @GetMapping("/{id}")
    public ResponseEntity<GlobalContent> getById(@PathVariable Long id) {
        GlobalContent content = globalContentService.getById(id);
        if (content == null) {
            return ResponseEntity.notFound().build();
        }
        applyChineseTranslation(content);
        return ResponseEntity.ok(content);
    }

    /**
     * 如果有中文翻译（titleCn / contentCn / summaryCn），
     * 将原文替换为中文翻译返回给前端；
     * 如果没有翻译，保持原文不变。
     * 原始字段和中文翻译字段均保留在 entity 中，前端可自行选择显示哪个。
     */
    private void applyChineseTranslation(GlobalContent content) {
        if (content.getTitleCn() != null && !content.getTitleCn().isEmpty()) {
            content.setTitle(content.getTitleCn());
        }
        if (content.getContentCn() != null && !content.getContentCn().isEmpty()) {
            content.setContent(content.getContentCn());
        }
        if (content.getSummaryCn() != null && !content.getSummaryCn().isEmpty()) {
            content.setSummary(content.getSummaryCn());
        }
    }

    @PostMapping
    public ResponseEntity<GlobalContent> create(@RequestBody GlobalContent content) {
        globalContentService.save(content);
        return ResponseEntity.ok(content);
    }

    @PutMapping("/{id}")
    public ResponseEntity<GlobalContent> update(@PathVariable Long id, @RequestBody GlobalContent content) {
        content.setId(id);
        if (!globalContentService.updateById(content)) {
            return ResponseEntity.notFound().build();
        }
        return ResponseEntity.ok(content);
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<Void> delete(@PathVariable Long id) {
        GlobalContent content = globalContentService.getById(id);
        if (content == null) {
            return ResponseEntity.notFound().build();
        }
        globalContentService.removeById(id);
        return ResponseEntity.ok().build();
    }

    @GetMapping("/top")
    public ResponseEntity<List<GlobalContent>> top(@RequestParam(defaultValue = "10") int limit) {
        QueryWrapper<GlobalContent> wrapper = new QueryWrapper<>();
        wrapper.orderByDesc("score").last("LIMIT " + limit);
        return ResponseEntity.ok(globalContentService.list(wrapper));
    }
}
