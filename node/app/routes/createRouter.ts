import glob from 'glob'
import express, { Router } from 'express'

const routes = () =>
  glob
    .sync('**/*.js', { cwd: `${__dirname}/` })
    .map((filename) => require(`./${filename}`))
    .filter((router) => Object.getPrototypeOf(router) == Router)
    .reduce(
      (rootRouter, router) => rootRouter.use(router),
      Router({ mergeParams: true }),
    )

export default routes
