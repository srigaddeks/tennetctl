"use client";

import React, { useEffect, useState } from 'react';
import { useTheme } from 'next-themes';
import { cn } from '../../../lib/utils';

// Import logos directly so the bundler can resolve paths correctly
import lightLogo from "../../../assets/logos/kreesalis.png";
import darkLogo from "../../../assets/logos/kreesalis_white_text.png";

export interface LogoProps extends React.ImgHTMLAttributes<HTMLImageElement> {
	className?: string;
}

export const Logo = ({ className, ...props }: LogoProps) => {
	const { theme, resolvedTheme } = useTheme();
	const [mounted, setMounted] = useState(false);

	// Avoid hydration mismatch
	useEffect(() => {
		setMounted(true);
	}, []);

	if (!mounted) {
		return (
			<div className={cn("relative flex items-center justify-center", className)}>
				<div className="h-full w-full bg-transparent" />
			</div>
		);
	}

	const isDark = resolvedTheme === 'dark' || theme === 'dark';
	const logoSrc = isDark ? darkLogo : lightLogo;
	
	// Handle Next.js image objects
	const src = typeof logoSrc === 'string' ? logoSrc : (logoSrc as any).src;

	return (
		<div className={cn("relative flex items-center justify-center", className)}>
			<img
				src={src}
				alt="Kreesalis Logo"
				className="object-contain h-full w-auto"
				{...props}
			/>
		</div>
	);
};
