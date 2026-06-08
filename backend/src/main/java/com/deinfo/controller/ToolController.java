package com.deinfo.controller;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.deinfo.dto.PageResult;
import com.deinfo.entity.ToolItem;
import com.deinfo.service.ToolItemService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/tools")
public class ToolController {

    private final ToolItemService toolItemService;

    public ToolController(ToolItemService toolItemService) {
        this.toolItemService = toolItemService;
    }

    @GetMapping
    public ResponseEntity<PageResult<ToolItem>> list(
            @RequestParam(required = false) String tag,
            @RequestParam(defaultValue = "1") int page,
            @RequestParam(defaultValue = "20") int size) {
        QueryWrapper<ToolItem> wrapper = new QueryWrapper<>();
        if (tag != null && !tag.isEmpty()) {
            wrapper.eq("tag", tag);
        }
        wrapper.orderByDesc("created_at");
        Page<ToolItem> pageParam = new Page<>(page, size);
        return ResponseEntity.ok(PageResult.from(toolItemService.page(pageParam, wrapper)));
    }

    @GetMapping("/{id}")
    public ResponseEntity<ToolItem> getById(@PathVariable Long id) {
        ToolItem toolItem = toolItemService.getById(id);
        if (toolItem == null) {
            return ResponseEntity.notFound().build();
        }
        return ResponseEntity.ok(toolItem);
    }

    @PostMapping
    public ResponseEntity<ToolItem> create(@RequestBody ToolItem toolItem) {
        toolItemService.save(toolItem);
        return ResponseEntity.ok(toolItem);
    }

    @PutMapping("/{id}")
    public ResponseEntity<ToolItem> update(@PathVariable Long id, @RequestBody ToolItem updated) {
        ToolItem existing = toolItemService.getById(id);
        if (existing == null) {
            return ResponseEntity.notFound().build();
        }
        updated.setId(id);
        toolItemService.updateById(updated);
        return ResponseEntity.ok(updated);
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<Void> delete(@PathVariable Long id) {
        ToolItem existing = toolItemService.getById(id);
        if (existing == null) {
            return ResponseEntity.notFound().build();
        }
        toolItemService.removeById(id);
        return ResponseEntity.ok().build();
    }
}
