package com.deinfo.dto;

import lombok.Data;

@Data
public class LoginResponse {
    private String token;
    private String role;
    private String username;

    public LoginResponse(String token, String role, String username) {
        this.token = token;
        this.role = role;
        this.username = username;
    }
}
