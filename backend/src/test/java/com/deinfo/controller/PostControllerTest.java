package com.deinfo.controller;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.deinfo.entity.Post;
import com.deinfo.service.PostService;
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

import java.util.List;

import static org.mockito.ArgumentMatchers.*;
import static org.mockito.BDDMockito.given;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@ExtendWith(MockitoExtension.class)
class PostControllerTest {

    private MockMvc mockMvc;

    @Mock
    private PostService postService;

    private ObjectMapper objectMapper;

    @BeforeEach
    void setUp() {
        objectMapper = new ObjectMapper();
        mockMvc = MockMvcBuilders.standaloneSetup(new PostController(postService)).build();
    }

    private Post createPost(Long id, String content) {
        Post post = new Post();
        post.setId(id);
        post.setUserId(1L);
        post.setContent(content);
        post.setStatus("approved");
        return post;
    }

    @Test
    @DisplayName("GET /api/posts 返回 PageResult")
    void list() throws Exception {
        Page<Post> page = new Page<>(1, 20);
        page.setRecords(List.of(createPost(1L, "测试帖子")));
        page.setTotal(1);
        given(postService.page(any(Page.class), any(QueryWrapper.class))).willReturn(page);

        mockMvc.perform(get("/api/posts"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.data.length()").value(1))
                .andExpect(jsonPath("$.total").value(1));
    }

    @Test
    @DisplayName("GET /api/posts/1 存在时返回")
    void getById_found() throws Exception {
        given(postService.getById(1L)).willReturn(createPost(1L, "帖子内容"));

        mockMvc.perform(get("/api/posts/1"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.content").value("帖子内容"));
    }

    @Test
    @DisplayName("GET /api/posts/999 不存在返回 404")
    void getById_notFound() throws Exception {
        given(postService.getById(999L)).willReturn(null);

        mockMvc.perform(get("/api/posts/999"))
                .andExpect(status().isNotFound());
    }

    @Test
    @DisplayName("POST /api/posts 创建帖子自动通过")
    void create() throws Exception {
        Post post = new Post();
        post.setContent("新帖子");
        given(postService.save(any(Post.class))).willReturn(true);

        mockMvc.perform(post("/api/posts")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(post)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.content").value("新帖子"))
                .andExpect(jsonPath("$.status").value("approved"));
    }
}
