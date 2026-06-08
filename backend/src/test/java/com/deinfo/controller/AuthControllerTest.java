package com.deinfo.controller;

import com.deinfo.dto.LoginRequest;
import com.deinfo.dto.LoginResponse;
import com.deinfo.entity.User;
import com.deinfo.mapper.UserMapper;
import com.deinfo.util.JwtUtil;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.http.MediaType;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;

import static org.mockito.ArgumentMatchers.*;
import static org.mockito.BDDMockito.given;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@ExtendWith(MockitoExtension.class)
class AuthControllerTest {

    private MockMvc mockMvc;

    @Mock
    private UserMapper userMapper;
    @Mock
    private JwtUtil jwtUtil;
    @Mock
    private PasswordEncoder passwordEncoder;

    private ObjectMapper objectMapper;

    @BeforeEach
    void setUp() {
        objectMapper = new ObjectMapper();
        AuthController controller = new AuthController(userMapper, jwtUtil, passwordEncoder);
        mockMvc = MockMvcBuilders.standaloneSetup(controller).build();
    }

    @Test
    @DisplayName("POST /api/auth/login - 成功登录返回 token")
    void login_success() throws Exception {
        User user = new User();
        user.setId(1L);
        user.setUsername("admin");
        user.setPassword("encoded");
        user.setRole("ADMIN");

        given(userMapper.selectOne(any())).willReturn(user);
        given(passwordEncoder.matches(eq("123456"), any())).willReturn(true);
        given(jwtUtil.generateToken("admin", "ADMIN")).willReturn("test-jwt-token");

        LoginRequest req = new LoginRequest();
        req.setUsername("admin");
        req.setPassword("123456");

        mockMvc.perform(post("/api/auth/login")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(req)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.token").value("test-jwt-token"))
                .andExpect(jsonPath("$.role").value("ADMIN"));
    }

    @Test
    @DisplayName("POST /api/auth/login - 密码错误返回 400")
    void login_invalidPassword() throws Exception {
        given(userMapper.selectOne(any())).willReturn(null);

        LoginRequest req = new LoginRequest();
        req.setUsername("admin");
        req.setPassword("wrong");

        mockMvc.perform(post("/api/auth/login")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(req)))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.error").value("invalid username or password"));
    }

    @Test
    @DisplayName("POST /api/auth/login - 缺少字段返回 400")
    void login_missingFields() throws Exception {
        LoginRequest req = new LoginRequest();

        mockMvc.perform(post("/api/auth/login")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(req)))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.error").value("username and password are required"));
    }

    @Test
    @DisplayName("POST /api/auth/register - 成功注册返回 token")
    void register_success() throws Exception {
        given(userMapper.selectCount(any())).willReturn(0L);
        given(passwordEncoder.encode("123456")).willReturn("encoded");
        given(jwtUtil.generateToken("newuser", "USER")).willReturn("new-jwt");

        LoginRequest req = new LoginRequest();
        req.setUsername("newuser");
        req.setPassword("123456");

        mockMvc.perform(post("/api/auth/register")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(req)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.token").value("new-jwt"));
    }

    @Test
    @DisplayName("POST /api/auth/register - 用户名重复返回 409")
    void register_duplicate() throws Exception {
        given(userMapper.selectCount(any())).willReturn(1L);

        LoginRequest req = new LoginRequest();
        req.setUsername("existing");
        req.setPassword("123456");

        mockMvc.perform(post("/api/auth/register")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(req)))
                .andExpect(status().isConflict())
                .andExpect(jsonPath("$.error").value("username already taken"));
    }
}
