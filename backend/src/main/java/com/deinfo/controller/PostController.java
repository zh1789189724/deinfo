package com.deinfo.controller;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.deinfo.dto.PageResult;
import com.deinfo.entity.Post;
import com.deinfo.service.PostService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/posts")
public class PostController {

    private final PostService postService;

    public PostController(PostService postService) {
        this.postService = postService;
    }

    @GetMapping
    public ResponseEntity<PageResult<Post>> list(
            @RequestParam(defaultValue = "1") int page,
            @RequestParam(defaultValue = "20") int size,
            @RequestParam(required = false) String category) {
        QueryWrapper<Post> wrapper = new QueryWrapper<>();
        wrapper.eq("status", "approved");
        if (category != null && !category.isEmpty()) {
            wrapper.eq("category", category);
        }
        wrapper.orderByDesc("created_at");
        return ResponseEntity.ok(PageResult.from(postService.page(new Page<>(page, size), wrapper)));
    }

    @GetMapping("/{id}")
    public ResponseEntity<Post> getById(@PathVariable Long id) {
        Post post = postService.getById(id);
        if (post == null) return ResponseEntity.notFound().build();
        return ResponseEntity.ok(post);
    }

    @PostMapping
    public ResponseEntity<Post> create(@RequestBody Post post) {
        post.setUserId(1L);
        post.setStatus("approved");
        post.setScore(0);
        postService.save(post);
        return ResponseEntity.ok(post);
    }
}
