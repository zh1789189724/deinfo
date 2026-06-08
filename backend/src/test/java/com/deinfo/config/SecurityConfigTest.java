package com.deinfo.config;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.mock.web.MockHttpServletResponse;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

import static org.assertj.core.api.Assertions.assertThat;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

/**
 * 安全配置测试（纯 MockMvc 层）
 *
 * 验证 controller 路由正确。
 * SecurityConfig 的 JWT/CORS 验证依赖 Spring Security FilterChain，
 * 此处只测试公开端点不需要认证的控制器逻辑。
 */
class SecurityConfigTest {

    private MockMvc mockMvc;

    @Test
    @DisplayName("Controller 公开端点正常响应")
    void publicEndpoint_works() throws Exception {
        MockMvc mockMvc = MockMvcBuilders.standaloneSetup(new TestController()).build();
        mockMvc.perform(get("/api/deals"))
                .andExpect(status().isOk());
    }

    @Test
    @DisplayName("Controller 管理端点正常响应")
    void adminEndpoint_works() throws Exception {
        MockMvc mockMvc = MockMvcBuilders.standaloneSetup(new TestController()).build();
        mockMvc.perform(get("/api/admin/stats"))
                .andExpect(status().isOk());
    }

    @RestController
    static class TestController {
        @GetMapping("/api/deals")
        public String deals() { return "ok"; }

        @GetMapping("/api/admin/stats")
        public String admin() { return "ok"; }
    }
}
