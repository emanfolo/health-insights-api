import * as admin from "firebase-admin";
import {
  likeRecipe,
  unlikeRecipe,
  recipeIsLiked,
  getUserLikedRecipes,
} from "./recipe";
import {cleanupUserData, ensureUserProfile} from "./user";
import {saveMealplan, unsaveMealplan} from "./mealplan";

admin.initializeApp();

export {
  likeRecipe,
  unlikeRecipe,
  recipeIsLiked,
  getUserLikedRecipes,
  cleanupUserData,
  ensureUserProfile,
  saveMealplan,
  unsaveMealplan,
};
