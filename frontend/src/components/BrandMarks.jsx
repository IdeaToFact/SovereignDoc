// Copyright (C) 2026 Idea To Fact LLC
// SPDX-License-Identifier: AGPL-3.0-only

import React from "react";

/**
 * 1. SovereignDoc App Logo (Document + Shield)
 */
export function SovereignDocLogo({ size = 28 }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 32 32"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      style={{ flexShrink: 0 }}
    >
      {/* Outer Sovereign Shield */}
      <path
        d="M16 3L5 7V14C5 21.5 10.2 27.8 16 30C21.8 27.8 27 21.5 27 14V7L16 3Z"
        fill="#0F172A"
        stroke="#10B981"
        strokeWidth="2"
        strokeLinejoin="round"
      />
      {/* Internal Document Sheet with Folded Corner */}
      <path d="M11 10H18L21 13V22H11V10Z" fill="#06B6D4" opacity="0.85" />
      <path d="M18 10V13H21" fill="#10B981" />
      {/* Grounded Citation Line */}
      <line x1="13" y1="17" x2="19" y2="17" stroke="#0F172A" strokeWidth="1.5" strokeLinecap="round" />
      <line x1="13" y1="19.5" x2="17" y2="19.5" stroke="#0F172A" strokeWidth="1.5" strokeLinecap="round" />
    </svg>
  );
}

/**
 * 2. AirGap Axis Platform Mark (Compass Shield)
 */
export function AirGapAxisMark({ size = 18 }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 32 32"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      style={{ flexShrink: 0 }}
    >
      {/* Outer Isolated Ring */}
      <circle cx="16" cy="16" r="13" stroke="#10B981" strokeWidth="2" strokeDasharray="18 4" />
      {/* Center Axis Node */}
      <circle cx="16" cy="16" r="4" fill="#06B6D4" />
      {/* Axis Crosshairs */}
      <line x1="16" y1="4" x2="16" y2="8" stroke="#10B981" strokeWidth="2" strokeLinecap="round" />
      <line x1="16" y1="24" x2="16" y2="28" stroke="#10B981" strokeWidth="2" strokeLinecap="round" />
      <line x1="4" y1="16" x2="8" y2="16" stroke="#10B981" strokeWidth="2" strokeLinecap="round" />
      <line x1="24" y1="16" x2="28" y2="16" stroke="#10B981" strokeWidth="2" strokeLinecap="round" />
    </svg>
  );
}

/**
 * 3. Idea To Fact LLC Parent Logo (Cube -> Checkmark)
 */
export function IdeaToFactLogo({ size = 22 }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 36 36"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      style={{ flexShrink: 0 }}
    >
      {/* Isometric Grounding Cube */}
      <path d="M18 4L30 11V25L18 32L6 25V11L18 4Z" stroke="#06B6D4" strokeWidth="2" strokeLinejoin="round" />
      <path d="M18 4V32" stroke="#06B6D4" strokeWidth="1.5" strokeDasharray="2 2" />
      <path d="M6 11L18 18L30 11" stroke="#06B6D4" strokeWidth="2" strokeLinejoin="round" />
      {/* Fact Verification Checkmark overlay */}
      <path
        d="M12 18L16.5 22.5L25 13.5"
        stroke="#10B981"
        strokeWidth="3.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

