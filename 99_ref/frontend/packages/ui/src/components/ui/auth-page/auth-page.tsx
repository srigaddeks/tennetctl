'use client';

import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Button } from '../button';

import {
	AtSignIcon,
	LockIcon,
	EyeIcon,
	EyeOffIcon,
} from 'lucide-react';
import { Input } from '../input';
import { Logo } from '../logo';
import { cn } from '../../../lib/utils';

export interface AuthPageProps {
	mode?: 'login' | 'register';
	onSubmit?: (email: string, password: string) => void;
	onGoogleLogin?: (idToken: string) => void;
	googleClientId?: string;
	isLoading?: boolean;
	error?: string | null;
	defaultEmail?: string;
	/** When true, the email field is pre-filled and cannot be changed (invite flow). */
	lockEmail?: boolean;
	/** When true, shows a loading skeleton in place of the email field while the invite email is being fetched. */
	emailLoading?: boolean;
}

export function AuthPage({ mode = 'login', onSubmit, onGoogleLogin, googleClientId, isLoading = false, error = null, defaultEmail, lockEmail = false, emailLoading = false }: AuthPageProps) {
	const isLogin = mode === 'login';
	const [email, setEmail] = useState(defaultEmail ?? '');
	const [password, setPassword] = useState('');

	// Sync email when defaultEmail arrives asynchronously (e.g. fetched after mount)
	React.useEffect(() => {
		if (defaultEmail && lockEmail) {
			setEmail(defaultEmail);
		}
	}, [defaultEmail, lockEmail]);
	const [showPassword, setShowPassword] = useState(false);
	const [showConfirmPassword, setShowConfirmPassword] = useState(false);
	const googleButtonRef = React.useRef<HTMLDivElement>(null);

	const handleSubmit = (e: React.FormEvent) => {
		e.preventDefault();
		if (onSubmit) {
			onSubmit(email, password);
		}
	};

	// Initialize Google Sign-In
	React.useEffect(() => {
		if (!googleClientId || !onGoogleLogin) return;

		/* eslint-disable @typescript-eslint/no-explicit-any */
		const win = window as any;

		const renderButton = () => {
			const el = googleButtonRef.current;
			if (!el || !win.google) return;
			const w = el.getBoundingClientRect().width || 400;
			win.google.accounts.id.renderButton(el, {
				theme: 'outline',
				size: 'large',
				width: Math.floor(w),
				text: isLogin ? 'signin_with' : 'signup_with',
			});
		};

		const initGoogle = () => {
			if (!win.google) return;
			win.google.accounts.id.initialize({
				client_id: googleClientId,
				callback: (response: { credential: string }) => {
					if (response.credential && onGoogleLogin) {
						onGoogleLogin(response.credential);
					}
				},
			});
			// Use RAF to ensure the DOM has painted before measuring width
			requestAnimationFrame(() => {
				requestAnimationFrame(renderButton);
			});
		};
		/* eslint-enable @typescript-eslint/no-explicit-any */

		if (win.google) {
			initGoogle();
		} else {
			// Avoid adding duplicate script tags
			const existing = document.querySelector('script[src="https://accounts.google.com/gsi/client"]');
			if (existing) {
				existing.addEventListener('load', initGoogle);
			} else {
				const script = document.createElement('script');
				script.src = 'https://accounts.google.com/gsi/client';
				script.async = true;
				script.defer = true;
				script.onload = initGoogle;
				document.head.appendChild(script);
			}
		}
	}, [googleClientId, onGoogleLogin, isLogin]);

	const config = {
		title: isLogin ? 'Welcome Back' : 'Create an Account',
		subtitle: isLogin
			? 'Enter your credentials to access your account'
			: 'Join Kreesalis to start managing your projects',
		primaryButton: isLogin ? 'Sign In' : 'Sign Up',
		footerText: isLogin ? "Don't have an account?" : 'Already have an account?',
		footerLink: isLogin ? 'Sign Up' : 'Sign In',
		footerHref: isLogin ? '/register' : '/login',
	};

	return (
		<main className="relative md:h-screen md:overflow-hidden lg:grid lg:grid-cols-2 bg-background">
			<div className="bg-muted/60 relative hidden h-full flex-col border-r p-10 lg:flex overflow-hidden">
				{/* Background Paths */}
				<div className="absolute inset-0 z-0">
					<FloatingPaths position={1} />
					<FloatingPaths position={-1} />
				</div>
				{/* Gradient Overlay */}
				<div className="from-background absolute inset-0 z-10 bg-gradient-to-t to-transparent opacity-50" />

				<div className="z-20 flex items-center gap-2">
					<Logo className="h-8" />
					<p className="text-xl font-semibold text-foreground font-secondary"></p>
				</div>
				<div className="z-20 mt-auto">
					<div className="max-w-lg">
						<p className="text-2xl font-medium leading-relaxed tracking-tight text-foreground/90 font-primary">
							K-Control is a comprehensive continuous compliance and runtime governance platform that automates security operations, eliminates manual audit preparation, and ensures your organization remains audit-ready 24/7.
						</p>
					</div>
				</div>
			</div>
			<div className="relative flex min-h-screen flex-col justify-center p-4 bg-background">
				<div
					aria-hidden
					className="absolute inset-0 isolate contain-strict -z-10 opacity-60"
				>
					<div className="bg-[radial-gradient(68.54%_68.72%_at_55.02%_31.46%,--theme(--color-foreground/.06)_0,hsla(0,0%,55%,.02)_50%,--theme(--color-foreground/.01)_80%)] absolute top-0 right-0 h-320 w-140 -translate-y-87.5 rounded-full" />
					<div className="bg-[radial-gradient(50%_50%_at_50%_50%,--theme(--color-foreground/.04)_0,--theme(--color-foreground/.01)_80%,transparent_100%)] absolute top-0 right-0 h-320 w-60 [translate:5%_-50%] rounded-full" />
					<div className="bg-[radial-gradient(50%_50%_at_50%_50%,--theme(--color-foreground/.04)_0,--theme(--color-foreground/.01)_80%,transparent_100%)] absolute top-0 right-0 h-320 w-60 -translate-y-87.5 rounded-full" />
				</div>
				<div className="mx-auto space-y-4 sm:w-sm w-full max-w-sm">
					<div className="flex items-center gap-2 lg:hidden">
						<Logo className="h-8" />
						<p className="text-xl font-semibold font-secondary">Kreesalis</p>
					</div>
					<div className="flex flex-col space-y-1">
						<h1 className="font-secondary text-2xl font-bold tracking-wide text-foreground">
							{config.title}
						</h1>
						<p className="text-muted-foreground text-base font-primary">
							{config.subtitle}
						</p>
					</div>
					{googleClientId && (
						<>
							<div ref={googleButtonRef} className="w-full min-h-[44px]" />
							<AuthSeparator />
						</>
					)}
					<form className="space-y-4" onSubmit={handleSubmit}>
						{error && (
							<div className="p-3 text-sm text-red-500 bg-red-100/10 border border-red-500/20 rounded-md">
								{error}
							</div>
						)}
						<div className="relative h-max">
							{emailLoading ? (
								<div className="flex items-center ps-9 h-10 rounded-md border border-zinc-200 dark:border-zinc-800 bg-muted animate-pulse">
									<span className="text-sm text-muted-foreground">Loading email…</span>
								</div>
							) : (
								<Input
									placeholder="Email"
									className={cn(
										"peer ps-9 border-zinc-200 dark:border-zinc-800",
										lockEmail && "text-foreground cursor-not-allowed"
									)}
									type="text"
									value={email}
									onChange={(e) => { if (!lockEmail) setEmail(e.target.value); }}
									readOnly={lockEmail}
									disabled={isLoading}
									required
									autoComplete="off"
									autoCorrect="off"
									autoCapitalize="off"
									spellCheck={false}
									data-1p-ignore="true"
									data-lpignore="true"
								/>
							)}
							<div className="text-muted-foreground pointer-events-none absolute inset-y-0 start-0 flex items-center justify-center ps-3 peer-disabled:opacity-50">
								<AtSignIcon className="size-4" aria-hidden="true" />
							</div>
						</div>

						<div className="relative h-max">
							<Input
								placeholder="Password"
								className="peer ps-9 pe-9 border-zinc-200 dark:border-zinc-800"
								type={showPassword ? 'text' : 'password'}
								value={password}
								onChange={(e) => setPassword(e.target.value)}
								disabled={isLoading}
								required
							/>
							<div className="text-muted-foreground pointer-events-none absolute inset-y-0 start-0 flex items-center justify-center ps-3 peer-disabled:opacity-50">
								<LockIcon className="size-4" aria-hidden="true" />
							</div>
							<button
								type="button"
								onClick={() => setShowPassword(!showPassword)}
								className="text-muted-foreground hover:text-foreground absolute inset-y-0 end-0 flex items-center justify-center pe-3 transition-colors focus:outline-none"
								aria-label={showPassword ? 'Hide password' : 'Show password'}
							>
								{showPassword ? (
									<EyeIcon className="size-4" aria-hidden="true" />
								) : (
									<EyeOffIcon className="size-4" aria-hidden="true" />
								)}
							</button>
						</div>

						{!isLogin && (
							<div className="relative h-max">
								<Input
									placeholder="Confirm Password"
									className="peer ps-9 pe-9 border-zinc-200 dark:border-zinc-800"
									type={showConfirmPassword ? 'text' : 'password'}
								/>
								<div className="text-muted-foreground pointer-events-none absolute inset-y-0 start-0 flex items-center justify-center ps-3 peer-disabled:opacity-50">
									<LockIcon className="size-4" aria-hidden="true" />
								</div>
								<button
									type="button"
									onClick={() => setShowConfirmPassword(!showConfirmPassword)}
									className="text-muted-foreground hover:text-foreground absolute inset-y-0 end-0 flex items-center justify-center pe-3 transition-colors focus:outline-none"
									aria-label={showConfirmPassword ? 'Hide password' : 'Show password'}
								>
									{showConfirmPassword ? (
										<EyeIcon className="size-4" aria-hidden="true" />
									) : (
										<EyeOffIcon className="size-4" aria-hidden="true" />
									)}
								</button>
							</div>
						)}

						{isLogin && (
							<div className="flex justify-end">
								<a href="/forgot-password" className="text-xs text-muted-foreground hover:text-primary transition-colors">
									Forgot password?
								</a>
							</div>
						)}

						<Button type="submit" className="w-full bg-[#4e5d72] hover:bg-[#3d4c5f] text-white border-0" disabled={isLoading}>
							<span className="font-primary">
								{isLoading ? "Please wait..." : config.primaryButton}
							</span>
						</Button>
					</form>

					{isLogin && (
						<div className="text-center space-y-1">
							<a
								href="/magic-link"
								className="text-sm text-muted-foreground hover:text-foreground transition-colors"
							>
								Sign in with a magic link instead
							</a>
							<div>
								<a
									href="/assignee/login"
									className="text-sm text-muted-foreground hover:text-foreground transition-colors"
								>
									Assigned evidence collector? Use assignee login
								</a>
							</div>
						</div>
					)}

					<div className="text-muted-foreground text-center text-sm">
						{config.footerText}{' '}
						<Button variant="link" className="px-0 py-0 h-auto font-semibold text-primary" asChild>
							<a href={config.footerHref}>{config.footerLink}</a>
						</Button>
					</div>
					<p className="text-muted-foreground mt-8 text-sm">
						By clicking continue, you agree to our{' '}
						<a
							href="#"
							className="hover:text-primary underline underline-offset-4"
						>
							Terms of Service
						</a>{' '}
						and{' '}
						<a
							href="#"
							className="hover:text-primary underline underline-offset-4"
						>
							Privacy Policy
						</a>
						.
					</p>
				</div>
			</div>
		</main>
	);
}

function FloatingPaths({ position }: { position: number }) {
	const [mounted, setMounted] = React.useState(false);

	React.useEffect(() => {
		setMounted(true);
	}, []);

	const paths = Array.from({ length: 36 }, (_, i) => ({
		id: i,
		d: `M-${380 - i * 5 * position} -${189 + i * 6}C-${380 - i * 5 * position
			} -${189 + i * 6} -${312 - i * 5 * position} ${216 - i * 6} ${152 - i * 5 * position
			} ${343 - i * 6}C${616 - i * 5 * position} ${470 - i * 6} ${684 - i * 5 * position
			} ${875 - i * 6} ${684 - i * 5 * position} ${875 - i * 6}`,
		width: 0.5 + i * 0.03,
	}));

	return (
		<div className="pointer-events-none absolute inset-0">
			<svg
				className="h-full w-full text-balck-900/40 dark:text-zinc-300/30"
				viewBox="0 0 696 316"
				fill="none"
			>
				<title>Background Paths</title>
				{paths.map((path) => (
					<motion.path
						key={path.id}
						d={path.d}
						stroke="currentColor"
						strokeWidth={path.width}
						strokeOpacity={0.2 + path.id * 0.03}
						initial={{ pathLength: 0.3, opacity: 0.6 }}
						animate={{
							pathLength: 1,
							opacity: [0.3, 0.6, 0.3],
							pathOffset: [0, 1, 0],
						}}
						transition={{
							duration: mounted ? 20 + Math.random() * 10 : 25,
							repeat: Number.POSITIVE_INFINITY,
							ease: 'linear',
						}}
					/>
				))}
			</svg>
		</div>
	);
}

const GoogleIcon = (props: React.ComponentProps<'svg'>) => (
	<svg
		xmlns="http://www.w3.org/2000/svg"
		viewBox="0 0 24 24"
		fill="currentColor"
		{...props}
	>
		<g>
			<path d="M12.479,14.265v-3.279h11.049c0.108,0.571,0.164,1.247,0.164,1.979c0,2.46-0.672,5.502-2.84,7.669   C18.744,22.829,16.051,24,12.483,24C5.869,24,0.308,18.613,0.308,12S5.869,0,12.483,0c3.659,0,6.265,1.436,8.223,3.307L18.392,5.62   c-1.404-1.317-3.307-2.341-5.913-2.341C7.65,3.279,3.873,7.171,3.873,12s3.777,8.721,8.606,8.721c3.132,0,4.916-1.258,6.059-2.401   c0.927-0.927,1.537-2.251,1.777-4.059L12.479,14.265z" />
		</g>
	</svg>
);

const AuthSeparator = () => {
	return (
		<div className="flex w-full items-center justify-center my-6">
			<div className="bg-border h-px w-full" />
			<span className="text-muted-foreground px-4 text-xs font-medium tracking-widest">OR</span>
			<div className="bg-border h-px w-full" />
		</div>
	);
};
